import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, Generic, NamedTuple, Optional, Union, cast

from pydantic import BaseModel
from typing_extensions import Unpack

from workflowai.core._common_types import BaseRunParams, OutputValidator
from workflowai.core.client._api import APIClient
from workflowai.core.client._models import (
    CreateAgentRequest,
    CreateAgentResponse,
    ReplyRequest,
    RunRequest,
    RunResponse,
)
from workflowai.core.client._types import RunParams
from workflowai.core.client._utils import (
    build_retryable_wait,
    global_default_version_reference,
    intolerant_validator,
    tolerant_validator,
)
from workflowai.core.domain.errors import BaseError, WorkflowAIError
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import AgentInput, AgentOutput
from workflowai.core.domain.tool import Tool
from workflowai.core.domain.tool_call import ToolCallRequest, ToolCallResult
from workflowai.core.domain.version_properties import VersionProperties
from workflowai.core.domain.version_reference import VersionReference
from workflowai.core.utils._tools import tool_schema


class Agent(Generic[AgentInput, AgentOutput]):
    _DEFAULT_MAX_ITERATIONS = 10

    def __init__(
        self,
        agent_id: str,
        input_cls: type[AgentInput],
        output_cls: type[AgentOutput],
        api: Union[APIClient, Callable[[], APIClient]],
        schema_id: Optional[int] = None,
        version: Optional[VersionReference] = None,
        tools: Optional[Iterable[Callable[..., Any]]] = None,
    ):
        self.agent_id = agent_id
        self.schema_id = schema_id
        self.input_cls = input_cls
        self.output_cls = output_cls
        self.version: VersionReference = version or global_default_version_reference()
        self._api = (lambda: api) if isinstance(api, APIClient) else api
        self._tools = self.build_tools(tools) if tools else None

    @classmethod
    def build_tools(cls, tools: Iterable[Callable[..., Any]]) -> dict[str, tuple[Tool, Callable[..., Any]]]:
        # TODO: we should be more tolerant with errors ?
        return {tool.__name__: (tool_schema(tool), tool) for tool in tools}

    @property
    def api(self) -> APIClient:
        return self._api()

    class _PreparedRun(NamedTuple):
        # would be nice to use a generic here, but python 3.9 does not support generic NamedTuple
        request: BaseModel
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
        if self._tools:
            dumped["enabled_tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "output_schema": tool.output_schema,
                }
                for tool, _ in self._tools.values()
            ]
        return dumped

    async def _prepare_run(self, task_input: AgentInput, stream: bool, **kwargs: Unpack[RunParams[AgentOutput]]):
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

    async def _prepare_reply(
        self,
        run_id: str,
        user_response: Optional[str],
        tool_results: Optional[Iterable[ToolCallResult]],
        stream: bool,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ):
        if not self.schema_id:
            raise ValueError("schema_id is required")
        version = self._sanitize_version(kwargs.get("version"))

        request = ReplyRequest(
            user_response=user_response,
            version=version,
            stream=stream,
            metadata=kwargs.get("metadata"),
            tool_results=[ReplyRequest.ToolResult.from_domain(tool_result) for tool_result in tool_results]
            if tool_results
            else None,
        )
        route = f"/v1/_/agents/{self.agent_id}/runs/{run_id}/reply"
        should_retry, wait_for_exception = build_retryable_wait(
            kwargs.get("max_retry_delay", 60),
            kwargs.get("max_retry_count", 1),
        )

        return self._PreparedRun(request, route, should_retry, wait_for_exception, self.schema_id)

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

    @classmethod
    async def _safe_execute_tool(cls, tool_call_request: ToolCallRequest, tool_func: Callable[..., Any]):
        try:
            output: Any = tool_func(**tool_call_request.input)
            if isinstance(output, Awaitable):
                output = await output
            return ToolCallResult(
                id=tool_call_request.id,
                output=output,
            )
        except Exception as e:  # noqa: BLE001
            return ToolCallResult(
                id=tool_call_request.id,
                error=str(e),
            )

    async def _execute_tools(
        self,
        run_id: str,
        tool_call_requests: Iterable[ToolCallRequest],
        current_iteration: int,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ):
        if not self._tools:
            return None

        executions: list[tuple[ToolCallRequest, Callable[..., Any]]] = []
        for tool_call_request in tool_call_requests:
            if tool_call_request.name not in self._tools:
                continue

            _, tool_func = self._tools[tool_call_request.name]
            executions.append((tool_call_request, tool_func))

        if not executions:
            return None

        # Executing all tools in parallel
        results = await asyncio.gather(
            *[self._safe_execute_tool(tool_call_request, tool_func) for tool_call_request, tool_func in executions],
        )
        return await self.reply(
            run_id=run_id,
            tool_results=results,
            current_iteration=current_iteration + 1,
            **kwargs,
        )

    async def _build_run(
        self,
        chunk: RunResponse,
        schema_id: int,
        validator: OutputValidator[AgentOutput],
        current_iteration: int,
        **kwargs: Unpack[BaseRunParams],
    ) -> Run[AgentOutput]:
        run = chunk.to_domain(self.agent_id, schema_id, validator)
        run._agent = self  # pyright: ignore [reportPrivateUsage]

        if run.tool_call_requests:
            if current_iteration >= kwargs.get("max_iterations", self._DEFAULT_MAX_ITERATIONS):
                raise WorkflowAIError(error=BaseError(message="max tool iterations reached"), response=None)
            with_reply = await self._execute_tools(
                run_id=run.id,
                tool_call_requests=run.tool_call_requests,
                current_iteration=current_iteration,
                validator=validator,
                **kwargs,
            )
            # Execute tools return None if there are actually no available tools to execute
            if with_reply:
                return with_reply

        return run

    async def run(
        self,
        task_input: AgentInput,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> Run[AgentOutput]:
        """Run the agent

        Args:
            task_input (AgentInput): the input to the task
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
            Union[TaskRun[AgentInput, AgentOutput], AsyncIterator[AgentOutput]]: the task run object
                or an async iterator of output objects
        """
        prepared_run = await self._prepare_run(task_input, stream=False, **kwargs)
        validator, new_kwargs = self._sanitize_validator(kwargs, intolerant_validator(self.output_cls))

        last_error = None
        while prepared_run.should_retry():
            try:
                res = await self.api.post(prepared_run.route, prepared_run.request, returns=RunResponse, run=True)
                return await self._build_run(
                    res,
                    prepared_run.schema_id,
                    validator,
                    current_iteration=0,
                    # TODO[test]: add test with custom validator
                    # We popped validator above
                    **new_kwargs,
                )
            except WorkflowAIError as e:  # noqa: PERF203
                last_error = e
                await prepared_run.wait_for_exception(e)

        raise last_error or WorkflowAIError(error=BaseError(message="max retries reached"), response=None)

    async def stream(
        self,
        task_input: AgentInput,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ):
        """Stream the output of the agent

        Args:
            task_input (AgentInput): the input to the task
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
            Union[TaskRun[AgentInput, AgentOutput], AsyncIterator[AgentOutput]]: the task run object
                or an async iterator of output objects
        """
        prepared_run = await self._prepare_run(task_input, stream=True, **kwargs)
        validator, new_kwargs = self._sanitize_validator(kwargs, tolerant_validator(self.output_cls))

        while prepared_run.should_retry():
            try:
                async for chunk in self.api.stream(
                    method="POST",
                    path=prepared_run.route,
                    data=prepared_run.request,
                    returns=RunResponse,
                    run=True,
                ):
                    yield await self._build_run(
                        chunk,
                        prepared_run.schema_id,
                        validator,
                        current_iteration=0,
                        **new_kwargs,
                    )
                return
            except WorkflowAIError as e:  # noqa: PERF203
                await prepared_run.wait_for_exception(e)

    async def reply(
        self,
        run_id: str,
        user_response: Optional[str] = None,
        tool_results: Optional[Iterable[ToolCallResult]] = None,
        current_iteration: int = 0,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ):
        prepared_run = await self._prepare_reply(run_id, user_response, tool_results, stream=False, **kwargs)
        validator, new_kwargs = self._sanitize_validator(kwargs, intolerant_validator(self.output_cls))

        res = await self.api.post(prepared_run.route, prepared_run.request, returns=RunResponse, run=True)
        return await self._build_run(
            res,
            prepared_run.schema_id,
            validator,
            current_iteration=current_iteration,
            **new_kwargs,
        )

    @classmethod
    def _sanitize_validator(cls, kwargs: RunParams[AgentOutput], default: OutputValidator[AgentOutput]):
        validator = kwargs.pop("validator", default)
        return validator, cast(BaseRunParams, kwargs)
