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

from workflowai.core.client.api import APIClient
from workflowai.core.client.models import (
    CreateTaskRequest,
    CreateTaskResponse,
    ExampleResponse,
    ImportExampleRequest,
    ImportRunRequest,
    PatchGroupRequest,
    RunRequest,
    RunTaskStreamChunk,
    TaskRunResponse,
)
from workflowai.core.client.utils import build_retryable_wait
from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.errors import BaseError, WorkflowAIError
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_example import TaskExample
from workflowai.core.domain.task_run import TaskRun
from workflowai.core.domain.task_version import TaskVersion
from workflowai.core.domain.task_version_reference import TaskVersionReference


class WorkflowAIClient:
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.additional_headers = {
            "x-workflowai-source": "sdk",
            "x-workflowai-language": "python",
            "x-workflowai-version": importlib.metadata.version("workflowai"),
        }
        self.api = APIClient(
            endpoint or os.getenv("WORKFLOWAI_API_URL", "https://api.workflowai.com"),
            api_key or os.getenv("WORKFLOWAI_API_KEY", ""),
            self.additional_headers,
        )

    async def register(self, task: Task[TaskInput, TaskOutput]):
        request = CreateTaskRequest(
            task_id=task.id or None,
            name=task.__class__.__name__.removesuffix("Task"),
            input_schema=task.input_class.model_json_schema(),
            output_schema=task.output_class.model_json_schema(),
        )

        res = await self.api.post("/tasks", request, returns=CreateTaskResponse)

        task.id = res.task_id
        task.schema_id = res.task_schema_id
        task.created_at = res.created_at

    async def _auto_register(self, task: Task[TaskInput, TaskOutput]):
        if not task.id or not task.schema_id:
            await self.register(task)

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        version: Optional[TaskVersionReference] = None,
        environment: Optional[str] = None,
        iteration: Optional[int] = None,
        stream: Literal[False] = False,
        use_cache: CacheUsage = "when_available",
        labels: Optional[set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> TaskRun[TaskInput, TaskOutput]: ...

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        version: Optional[TaskVersionReference] = None,
        environment: Optional[str] = None,
        iteration: Optional[int] = None,
        stream: Literal[True] = True,
        use_cache: CacheUsage = "when_available",
        labels: Optional[set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> AsyncIterator[TaskOutput]: ...

    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        version: Optional[TaskVersionReference] = None,
        environment: Optional[str] = None,
        iteration: Optional[int] = None,
        stream: bool = False,
        use_cache: CacheUsage = "when_available",
        labels: Optional[set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> Union[TaskRun[TaskInput, TaskOutput], AsyncIterator[TaskOutput]]:
        await self._auto_register(task)

        if version:
            group_ref = version
        elif environment:
            group_ref = TaskVersionReference(alias=f"environment={environment}")
        elif iteration:
            group_ref = TaskVersionReference(iteration=iteration)
        else:
            group_ref = task.version

        request = RunRequest(
            task_input=task_input.model_dump(),
            group=group_ref,
            stream=stream,
            use_cache=use_cache,
            labels=labels,
            metadata=metadata,
        )

        route = f"/tasks/{task.id}/schemas/{task.schema_id}/run"
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
                res = await self.api.post(route, request, returns=TaskRunResponse)
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
                    returns=RunTaskStreamChunk,
                ):
                    yield task.output_class.model_construct(None, **chunk.task_output)
                return
            except WorkflowAIError as e:  # noqa: PERF203
                await wait_for_exception(e)

    async def import_run(
        self,
        run: TaskRun[TaskInput, TaskOutput],
    ) -> TaskRun[TaskInput, TaskOutput]:
        await self._auto_register(run.task)

        request = ImportRunRequest.from_domain(run)
        route = f"/tasks/{run.task.id}/schemas/{run.task.schema_id}/runs"
        res = await self.api.post(route, request, returns=TaskRunResponse)
        return res.to_domain(run.task)

    async def import_example(
        self,
        example: TaskExample[TaskInput, TaskOutput],
    ) -> TaskExample[TaskInput, TaskOutput]:
        await self._auto_register(example.task)

        request = ImportExampleRequest.from_domain(example)
        route = f"/tasks/{example.task.id}/schemas/{example.task.schema_id}/examples"
        res = await self.api.post(route, request, returns=ExampleResponse)
        return res.to_domain(example.task)

    async def deploy_version(
        self,
        task: Task[TaskInput, TaskOutput],
        iteration: int,
        environment: str,
    ) -> TaskVersion:
        await self._auto_register(task)

        route = f"/tasks/{task.id}/schemas/{task.schema_id}/groups/{iteration}"
        req = PatchGroupRequest(add_alias=f"environment={environment}")
        res = await self.api.patch(route, req, returns=TaskVersion)
        return res
