import importlib.metadata
import os
from collections.abc import Awaitable, Callable
from typing import (
    Any,
    AsyncIterator,
    Literal,
    Optional,
    Union,
    overload,
)

from workflowai.core.client import Client
from workflowai.core.client.api import APIClient
from workflowai.core.client.models import (
    RunRequest,
    RunResponse,
    RunStreamChunk,
)
from workflowai.core.client.utils import build_retryable_wait
from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.errors import BaseError, WorkflowAIError
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_run import Run, RunChunk
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
        version: Optional[VersionReference] = None,
        use_cache: CacheUsage = "when_available",
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> Run[TaskOutput]: ...

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: Literal[True] = True,
        version: Optional[VersionReference] = None,
        use_cache: CacheUsage = "when_available",
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> AsyncIterator[Union[RunChunk[TaskOutput], Run[TaskOutput]]]: ...

    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: bool = False,
        version: Optional[VersionReference] = None,
        use_cache: CacheUsage = "when_available",
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> Union[Run[TaskOutput], AsyncIterator[Union[RunChunk[TaskOutput], Run[TaskOutput]]]]:
        request = RunRequest(
            task_input=task_input.model_dump(by_alias=True),
            version=version or task.version,
            stream=stream,
            use_cache=use_cache,
            metadata=metadata,
        )

        route = f"/v1/_/tasks/{task.id}/schemas/{task.schema_id}/run"
        should_retry, wait_for_exception = build_retryable_wait(max_retry_delay, max_retry_count)

        if not stream:
            return await self._retriable_run(
                route,
                request,
                task,
                should_retry=should_retry,
                wait_for_exception=wait_for_exception,
            )

        return self._retriable_stream(
            route,
            request,
            task,
            should_retry=should_retry,
            wait_for_exception=wait_for_exception,
        )

    async def _retriable_run(
        self,
        route: str,
        request: RunRequest,
        task: Task[TaskInput, TaskOutput],
        should_retry: Callable[[], bool],
        wait_for_exception: Callable[[WorkflowAIError], Awaitable[None]],
    ):
        last_error = None
        while should_retry():
            try:
                res = await self.api.post(route, request, returns=RunResponse)
                return res.to_domain(task)
            except WorkflowAIError as e:  # noqa: PERF203
                last_error = e
                await wait_for_exception(e)

        raise last_error or WorkflowAIError(error=BaseError(message="max retries reached"), response=None)

    async def _retriable_stream(
        self,
        route: str,
        request: RunRequest,
        task: Task[TaskInput, TaskOutput],
        should_retry: Callable[[], bool],
        wait_for_exception: Callable[[WorkflowAIError], Awaitable[None]],
    ):
        while should_retry():
            try:
                async for chunk in self.api.stream(
                    method="POST",
                    path=route,
                    data=request,
                    returns=RunStreamChunk,
                ):
                    yield chunk.to_domain(task)
                return
            except WorkflowAIError as e:  # noqa: PERF203
                await wait_for_exception(e)
