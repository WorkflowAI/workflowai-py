import asyncio
from asyncio.log import logger
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, Generic, NamedTuple, Optional, Union, cast

from pydantic import BaseModel
from typing_extensions import Unpack

from workflowai.core._common_types import BaseRunParams, OutputValidator, VersionRunParams
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
from workflowai.core.utils._schema_generator import JsonSchemaGenerator


class Agent(Generic[AgentInput, AgentOutput]):
    """A class representing an AI agent that can process inputs and generate outputs.

    The Agent class provides functionality to run AI-powered tasks with support for streaming,
    tool execution, and version management. This class is not intended to be used directly,
    instead use the `agent` decorator to create an agent.

    Args:
        agent_id (str): Unique identifier for the agent.
        input_cls (type[AgentInput]): The Pydantic model class defining the expected input structure.
        output_cls (type[AgentOutput]): The Pydantic model class defining the expected output structure.
        api (Union[APIClient, Callable[[], APIClient]]): The API client instance or factory function.
        schema_id (Optional[int], optional): The schema ID for the agent. Defaults to None.
        version (Optional[VersionReference], optional): The version reference for the agent.
            If not provided, uses the global default version. Defaults to None.
        tools (Optional[Iterable[Callable[..., Any]]], optional): Collection of tool functions
            that the agent can use. Defaults to None.

    Attributes:
        agent_id (str): The agent's unique identifier.
        schema_id (Optional[int]): The schema ID associated with the agent.
        input_cls (type[AgentInput]): The input model class.
        output_cls (type[AgentOutput]): The output model class.
        version (VersionReference): The version reference for the agent.

    Example:
        ```python
        from pydantic import BaseModel

        class MyInput(BaseModel):
            query: str

        class MyOutput(BaseModel):
            response: str

        agent = Agent(
            agent_id="my-agent",
            input_cls=MyInput,
            output_cls=MyOutput,
            api=api_client
        )

        result = await agent.run(MyInput(query="Hello"))
        ```
    """

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
    def build_tools(cls, tools: Iterable[Callable[..., Any]]):
        # TODO: we should be more tolerant with errors ?
        return {tool.__name__: Tool.from_fn(tool) for tool in tools}

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

    def _sanitize_version(self, params: VersionRunParams) -> Union[str, int, dict[str, Any]]:
        version = params.get("version")
        model = params.get("model")
        instructions = params.get("instructions")
        temperature = params.get("temperature")

        has_property_overrides = bool(model or instructions or temperature)

        if not version:
            # If versions is not specified, we fill with the default agent version only if
            # there are no additional properties
            version = self.version if not has_property_overrides else VersionProperties()

        if not isinstance(version, VersionProperties):
            if has_property_overrides or self._tools:
                logger.warning("Property overrides are ignored when version is not a VersionProperties")
            return version

        dumped = version.model_dump(by_alias=True, exclude_unset=True)

        if not dumped.get("model"):
            # We always provide a default model since it is required by the API
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
                for tool in self._tools.values()
            ]
        # Finally we apply the property overrides
        if model:
            dumped["model"] = model
        if instructions:
            dumped["instructions"] = instructions
        if temperature:
            dumped["temperature"] = temperature
        return dumped

    async def _prepare_run(self, agent_input: AgentInput, stream: bool, **kwargs: Unpack[RunParams[AgentOutput]]):
        schema_id = self.schema_id
        if not schema_id:
            schema_id = await self.register()

        version = self._sanitize_version(kwargs)

        request = RunRequest(
            id=kwargs.get("id"),
            task_input=agent_input.model_dump(by_alias=True),
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
        user_message: Optional[str],
        tool_results: Optional[Iterable[ToolCallResult]],
        stream: bool,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ):
        if not self.schema_id:
            raise ValueError("schema_id is required")
        version = self._sanitize_version(kwargs)

        request = ReplyRequest(
            user_message=user_message,
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
        """
        Registers the agent and returns the schema id. This function is called
        when the agent is first used and the result is cached in the agent's definition.
        """
        res = await self.api.post(
            "/v1/_/agents",
            CreateAgentRequest(
                id=self.agent_id,
                input_schema=self.input_cls.model_json_schema(
                    mode="serialization",
                    schema_generator=JsonSchemaGenerator,
                ),
                output_schema=self.output_cls.model_json_schema(
                    mode="validation",
                    schema_generator=JsonSchemaGenerator,
                ),
            ),
            returns=CreateAgentResponse,
        )
        self.schema_id = res.schema_id
        return res.schema_id

    @classmethod
    async def _safe_execute_tool(cls, tool_call_request: ToolCallRequest, tool: Tool):
        try:
            output = await tool(tool_call_request.input)
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

        executions: list[tuple[ToolCallRequest, Tool]] = []
        for tool_call_request in tool_call_requests:
            if tool_call_request.name not in self._tools:
                continue

            tool = self._tools[tool_call_request.name]
            executions.append((tool_call_request, tool))

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

    def _build_run_no_tools(
        self,
        chunk: RunResponse,
        schema_id: int,
        validator: OutputValidator[AgentOutput],
    ) -> Run[AgentOutput]:
        run = chunk.to_domain(self.agent_id, schema_id, validator)
        run._agent = self  # pyright: ignore [reportPrivateUsage]
        return run

    async def _build_run(
        self,
        chunk: RunResponse,
        schema_id: int,
        validator: OutputValidator[AgentOutput],
        current_iteration: int,
        **kwargs: Unpack[BaseRunParams],
    ) -> Run[AgentOutput]:
        run = self._build_run_no_tools(chunk, schema_id, validator)

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
        agent_input: AgentInput,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> Run[AgentOutput]:
        """Run the agent

        Args:
            agent_input (AgentInput): The input to the task.
            id (Optional[str]): A user defined ID for the run. The ID must be a UUID7, ordered by creation time.
                If not provided, a UUID7 will be assigned by the server.
            model (Optional[str]): The model to use for this run. Overrides the version's model if provided.
            version (Optional[VersionReference]): The version of the task to run. If not provided,
                the version defined in the task is used.
            instructions (Optional[str]): Custom instructions for this run. Overrides the version's instructions if
                provided.
            temperature (Optional[float]): The temperature to use for this run. Overrides the version's temperature if
                provided.
            use_cache (CacheUsage, optional): How to use the cache. Defaults to "auto".
                "auto" (default): if a previous run exists with the same version and input, and if
                    the temperature is 0, the cached output is returned
                "always": the cached output is returned when available, regardless
                    of the temperature value
                "never": the cache is never used
            labels (Optional[set[str]], optional): Labels are deprecated, please use metadata instead.
            metadata (Optional[dict[str, Any]], optional): A dictionary of metadata to attach to the run.
            max_retry_delay (Optional[float], optional): The maximum delay between retries in milliseconds.
                Defaults to 60000.
            max_retry_count (Optional[float], optional): The maximum number of retry attempts. Defaults to 1.
            max_tool_iterations (Optional[int], optional): Maximum number of tool iteration cycles. Defaults to 10.
            validator (Optional[OutputValidator[AgentOutput]], optional): Custom validator for the output.

        Returns:
            Run[AgentOutput]: The task run object.
        """
        prepared_run = await self._prepare_run(agent_input, stream=False, **kwargs)
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
        agent_input: AgentInput,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ):
        """Stream the output of the agent

        Args:
            agent_input (AgentInput): The input to the task.
            id (Optional[str]): A user defined ID for the run. The ID must be a UUID7, ordered by creation time.
                If not provided, a UUID7 will be assigned by the server.
            model (Optional[str]): The model to use for this run. Overrides the version's model if provided.
            version (Optional[VersionReference]): The version of the task to run. If not provided,
                the version defined in the task is used.
            instructions (Optional[str]): Custom instructions for this run.
                Overrides the version's instructions if provided.
            temperature (Optional[float]): The temperature to use for this run.
                Overrides the version's temperature if provided.
            use_cache (CacheUsage, optional): How to use the cache. Defaults to "auto".
                "auto" (default): if a previous run exists with the same version and input, and if
                    the temperature is 0, the cached output is returned
                "always": the cached output is returned when available, regardless
                    of the temperature value
                "never": the cache is never used
            labels (Optional[set[str]], optional): Labels are deprecated, please use metadata instead.
            metadata (Optional[dict[str, Any]], optional): A dictionary of metadata to attach to the run.
            max_retry_delay (Optional[float], optional): The maximum delay between retries in milliseconds.
                Defaults to 60000.
            max_retry_count (Optional[float], optional): The maximum number of retry attempts. Defaults to 1.
            max_tool_iterations (Optional[int], optional): Maximum number of tool iteration cycles. Defaults to 10.
            validator (Optional[OutputValidator[AgentOutput]], optional): Custom validator for the output.

        Returns:
            AsyncIterator[Run[AgentOutput]]: An async iterator yielding task run objects.
        """
        prepared_run = await self._prepare_run(agent_input, stream=True, **kwargs)
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
        user_message: Optional[str] = None,
        tool_results: Optional[Iterable[ToolCallResult]] = None,
        current_iteration: int = 0,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ):
        """Reply to a run to provide additional information or context.

        Args:
            run_id (str): The id of the run to reply to.
            user_message (Optional[str]): The message to reply with.
            tool_results (Optional[Iterable[ToolCallResult]]): The results of the tool calls.
            **kwargs: Additional keyword arguments.

        Returns:
            Run[AgentOutput]: The task run object.
        """

        prepared_run = await self._prepare_reply(run_id, user_message, tool_results, stream=False, **kwargs)
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
