import importlib.metadata
import logging
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

from workflowai.core.client._api import APIClient
from workflowai.core.client._fn_utils import task_wrapper
from workflowai.core.client._models import (
    RunRequest,
    RunResponse,
)
from workflowai.core.client._types import (
    OutputValidator,
    RunParams,
)
from workflowai.core.client._utils import build_retryable_wait, tolerant_validator
from workflowai.core.domain.errors import BaseError, WorkflowAIError
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.version_reference import VersionReference

_logger = logging.getLogger("WorkflowAI")


def _compute_default_version_reference() -> VersionReference:
    version = os.getenv("WORKFLOWAI_DEFAULT_VERSION")
    if not version:
        return "production"

    if version in {"dev", "staging", "production"}:
        return version  # pyright: ignore [reportReturnType]

    try:
        return int(version)
    except ValueError:
        pass

    _logger.warning("Invalid default version: %s", version)

    return "production"


class WorkflowAIClient:
    def __init__(
        self,
        api_key: str,
        endpoint: Optional[str] = None,
        default_version: Optional[VersionReference] = None,
    ):
        self.additional_headers = {
            "x-workflowai-source": "sdk",
            "x-workflowai-language": "python",
            "x-workflowai-version": importlib.metadata.version("workflowai"),
        }
        self.api = APIClient(endpoint or "https://run.workflowai.com", api_key, self.additional_headers)
        self.default_version: VersionReference = default_version or _compute_default_version_reference()

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
            version=kwargs.get("version") or task.version or self.default_version,
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
                task_id=task.id,
                task_schema_id=task.schema_id,
                validator=kwargs.get("validator") or task.output_class.model_validate,
            )

        return self._retriable_stream(
            route,
            request,
            should_retry=should_retry,
            wait_for_exception=wait_for_exception,
            task_id=task.id,
            task_schema_id=task.schema_id,
            validator=kwargs.get("validator") or tolerant_validator(task.output_class),
        )

    async def _retriable_run(
        self,
        route: str,
        request: RunRequest,
        should_retry: Callable[[], bool],
        wait_for_exception: Callable[[WorkflowAIError], Awaitable[None]],
        task_id: str,
        task_schema_id: int,
        validator: OutputValidator[TaskOutput],
    ):
        last_error = None
        while should_retry():
            try:
                res = await self.api.post(route, request, returns=RunResponse)
                return res.to_domain(task_id, task_schema_id, validator)
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
        task_id: str,
        task_schema_id: int,
        validator: OutputValidator[TaskOutput],
    ):
        while should_retry():
            try:
                async for chunk in self.api.stream(
                    method="POST",
                    path=route,
                    data=request,
                    returns=RunResponse,
                ):
                    yield chunk.to_domain(task_id, task_schema_id, validator)
                return
            except WorkflowAIError as e:  # noqa: PERF203
                await wait_for_exception(e)

    def task(
        self,
        schema_id: int,
        task_id: Optional[str] = None,
        version: Optional[VersionReference] = None,
    ):
        return task_wrapper(lambda: self, schema_id, task_id=task_id, version=version)
