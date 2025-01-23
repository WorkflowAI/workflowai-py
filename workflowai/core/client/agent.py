from collections.abc import Awaitable, Callable
from typing import Any, Generic, NamedTuple, Optional, Union

from typing_extensions import Unpack

from workflowai.core.client._api import APIClient
from workflowai.core.client._models import CreateAgentRequest, CreateAgentResponse, RunRequest, RunResponse
from workflowai.core.client._types import RunParams
from workflowai.core.client._utils import build_retryable_wait, global_default_version_reference, tolerant_validator
from workflowai.core.domain.errors import BaseError, WorkflowAIError
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import TaskInput, TaskOutput
from workflowai.core.domain.version_properties import VersionProperties
from workflowai.core.domain.version_reference import VersionReference


class Agent(Generic[TaskInput, TaskOutput]):
    def __init__(
        self,
        agent_id: str,
        input_cls: type[TaskInput],
        output_cls: type[TaskOutput],
        api: Union[APIClient, Callable[[], APIClient]],
        schema_id: Optional[int] = None,
        version: Optional[VersionReference] = None,
    ):
        self.agent_id = agent_id
        self.schema_id = schema_id
        self.input_cls = input_cls
        self.output_cls = output_cls
        self.version: VersionReference = version or global_default_version_reference()
        self._api = (lambda: api) if isinstance(api, APIClient) else api

    @property
    def api(self) -> APIClient:
        return self._api()

    class _PreparedRun(NamedTuple):
        request: RunRequest
        route: str
        should_retry: Callable[[], bool]
        wait_for_exception: Callable[[WorkflowAIError], Awaitable[None]]
        schema_id: int

    def _sanitize_version(self, version: Optional[VersionReference]) -> Union[str, int, dict[str, Any]]:
        if not version:
            version = self.version
        if not isinstance(version, VersionProperties):
            return version

        dumped = version.model_dump(by_alias=True)
        if not dumped.get("model"):
            import workflowai

            dumped["model"] = workflowai.DEFAULT_MODEL
        return dumped

    async def _prepare_run(self, task_input: TaskInput, stream: bool, **kwargs: Unpack[RunParams[TaskOutput]]):
        schema_id = self.schema_id
        if not schema_id:
            schema_id = await self.register()

        version = self._sanitize_version(kwargs.get("version"))

        request = RunRequest(
            task_input=task_input.model_dump(by_alias=True),
            version=version,
            stream=stream,
            use_cache=kwargs.get("use_cache"),
            metadata=kwargs.get("metadata"),
            labels=kwargs.get("labels"),
        )

        route = f"/v1/_/agents/{self.agent_id}/schemas/{self.schema_id}/run"
        should_retry, wait_for_exception = build_retryable_wait(
            kwargs.get("max_retry_delay", 60),
            kwargs.get("max_retry_count", 1),
        )
        return self._PreparedRun(request, route, should_retry, wait_for_exception, schema_id)

    async def register(self):
        """Registers the agent and returns the schema id"""
        res = await self.api.post(
            "/v1/_/agents",
            CreateAgentRequest(
                id=self.agent_id,
                input_schema=self.input_cls.model_json_schema(),
                output_schema=self.output_cls.model_json_schema(),
            ),
            returns=CreateAgentResponse,
        )
        self.schema_id = res.schema_id
        return res.schema_id

    async def run(
        self,
        task_input: TaskInput,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> Run[TaskOutput]:
        """Run the agent

        Args:
            task_input (TaskInput): the input to the task
            version (Optional[TaskVersionReference], optional): the version of the task to run. If not provided,
                the version defined in the task is used. Defaults to None.
            use_cache (CacheUsage, optional): how to use the cache. Defaults to "auto".
                "auto" (default): if a previous run exists with the same version and input, and if
                    the temperature is 0, the cached output is returned
                "always": the cached output is returned when available, regardless
                    of the temperature value
                "never": the cache is never used
            labels (Optional[set[str]], optional): a set of labels to attach to the run.
                Labels are indexed and searchable. Defaults to None.
            metadata (Optional[dict[str, Any]], optional): a dictionary of metadata to attach to the run.
                Defaults to None.
            retry_delay (int, optional): The initial delay between retries in milliseconds. Defaults to 5000.
            max_retry_delay (int, optional): The maximum delay between retries in milliseconds. Defaults to 60000.
            max_retry_count (int, optional): The maximum number of retry attempts. Defaults to 1.

        Returns:
            Union[TaskRun[TaskInput, TaskOutput], AsyncIterator[TaskOutput]]: the task run object
                or an async iterator of output objects
        """
        prepared_run = await self._prepare_run(task_input, stream=False, **kwargs)
        validator = kwargs.get("validator") or self.output_cls.model_validate

        last_error = None
        while prepared_run.should_retry():
            try:
                res = await self.api.post(prepared_run.route, prepared_run.request, returns=RunResponse)
                return res.to_domain(self.agent_id, prepared_run.schema_id, validator)
            except WorkflowAIError as e:  # noqa: PERF203
                last_error = e
                await prepared_run.wait_for_exception(e)

        raise last_error or WorkflowAIError(error=BaseError(message="max retries reached"), response=None)

    async def stream(
        self,
        task_input: TaskInput,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ):
        """Stream the output of the agent

        Args:
            task_input (TaskInput): the input to the task
            version (Optional[TaskVersionReference], optional): the version of the task to run. If not provided,
                the version defined in the task is used. Defaults to None.
            use_cache (CacheUsage, optional): how to use the cache. Defaults to "auto".
                "auto" (default): if a previous run exists with the same version and input, and if
                    the temperature is 0, the cached output is returned
                "always": the cached output is returned when available, regardless
                    of the temperature value
                "never": the cache is never used
            labels (Optional[set[str]], optional): a set of labels to attach to the run.
                Labels are indexed and searchable. Defaults to None.
            metadata (Optional[dict[str, Any]], optional): a dictionary of metadata to attach to the run.
                Defaults to None.
            retry_delay (int, optional): The initial delay between retries in milliseconds. Defaults to 5000.
            max_retry_delay (int, optional): The maximum delay between retries in milliseconds. Defaults to 60000.
            max_retry_count (int, optional): The maximum number of retry attempts. Defaults to 1.

        Returns:
            Union[TaskRun[TaskInput, TaskOutput], AsyncIterator[TaskOutput]]: the task run object
                or an async iterator of output objects
        """
        prepared_run = await self._prepare_run(task_input, stream=True, **kwargs)
        validator = kwargs.get("validator") or tolerant_validator(self.output_cls)

        while prepared_run.should_retry():
            try:
                async for chunk in self.api.stream(
                    method="POST",
                    path=prepared_run.route,
                    data=prepared_run.request,
                    returns=RunResponse,
                ):
                    yield chunk.to_domain(self.agent_id, prepared_run.schema_id, validator)
                return
            except WorkflowAIError as e:  # noqa: PERF203
                await prepared_run.wait_for_exception(e)
