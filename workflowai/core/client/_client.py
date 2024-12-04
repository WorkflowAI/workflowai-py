import functools
import importlib.metadata
import os
from collections.abc import Awaitable, Callable
from typing import (
    AsyncIterator,
    Literal,
    Optional,
    Union,
    overload,
)

from typing_extensions import Unpack

from workflowai.core.client import Client
from workflowai.core.client._api import APIClient
from workflowai.core.client._fn_utils import wrap_run_template
from workflowai.core.client._models import (
    RunRequest,
    RunResponse,
    RunStreamChunk,
)
from workflowai.core.client._types import (
    FinalRunTemplate,
    OutputValidator,
    RunParams,
    RunTemplate,
    TaskDecorator,
)
from workflowai.core.client._utils import build_retryable_wait, tolerant_validator
from workflowai.core.domain.errors import BaseError, WorkflowAIError
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_run import Run
from workflowai.core.domain.task_version_reference import VersionReference


class WorkflowAIClient(Client):
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.additional_headers = {
            "x-workflowai-source": "sdk",
            "x-workflowai-language": "python",
            "x-workflowai-version": importlib.metadata.version("workflowai"),
        }
        self.api = APIClient(
            endpoint or os.getenv("WORKFLOWAI_API_URL", "https://run.workflowai.com"),
            api_key or os.getenv("WORKFLOWAI_API_KEY", ""),
            self.additional_headers,
        )

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: Literal[False] = False,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> Run[TaskOutput]: ...

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: Literal[True] = True,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> AsyncIterator[Run[TaskOutput]]: ...

    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: bool = False,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> Union[Run[TaskOutput], AsyncIterator[Run[TaskOutput]]]:
        request = RunRequest(
            task_input=task_input.model_dump(by_alias=True),
            version=kwargs.get("version") or task.version,
            stream=stream,
            use_cache=kwargs.get("use_cache"),
            metadata=kwargs.get("metadata"),
        )

        route = f"/v1/_/tasks/{task.id}/schemas/{task.schema_id}/run"
        should_retry, wait_for_exception = build_retryable_wait(
            kwargs.get("max_retry_delay", 60),
            kwargs.get("max_retry_count", 1),
        )

        if not stream:
            return await self._retriable_run(
                route,
                request,
                should_retry=should_retry,
                wait_for_exception=wait_for_exception,
                validator=kwargs.get("validator") or task.output_class.model_validate,
            )

        return self._retriable_stream(
            route,
            request,
            should_retry=should_retry,
            wait_for_exception=wait_for_exception,
            validator=kwargs.get("validator") or tolerant_validator(task.output_class),
        )

    async def _retriable_run(
        self,
        route: str,
        request: RunRequest,
        should_retry: Callable[[], bool],
        wait_for_exception: Callable[[WorkflowAIError], Awaitable[None]],
        validator: OutputValidator[TaskOutput],
    ):
        last_error = None
        while should_retry():
            try:
                res = await self.api.post(route, request, returns=RunResponse)
                return res.to_domain(validator)
            except WorkflowAIError as e:  # noqa: PERF203
                last_error = e
                await wait_for_exception(e)

        raise last_error or WorkflowAIError(error=BaseError(message="max retries reached"), response=None)

    async def _retriable_stream(
        self,
        route: str,
        request: RunRequest,
        should_retry: Callable[[], bool],
        wait_for_exception: Callable[[WorkflowAIError], Awaitable[None]],
        validator: OutputValidator[TaskOutput],
    ):
        while should_retry():
            try:
                async for chunk in self.api.stream(
                    method="POST",
                    path=route,
                    data=request,
                    returns=RunStreamChunk,
                ):
                    yield chunk.to_domain(validator)
                return
            except WorkflowAIError as e:  # noqa: PERF203
                await wait_for_exception(e)

    def task(self, id: str, schema_id: int, version: VersionReference = "production") -> TaskDecorator:  # noqa: A002
        def wrap(fn: RunTemplate[TaskInput, TaskOutput]) -> FinalRunTemplate[TaskInput, TaskOutput]:
            return functools.wraps(fn)(wrap_run_template(self, id, schema_id, version, fn))  # pyright: ignore [reportReturnType]

        return wrap  # pyright: ignore [reportReturnType]
