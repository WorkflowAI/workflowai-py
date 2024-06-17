import os
from typing import Any, AsyncIterator, Optional, Union

from workflowai.core.client.api import APIClient
from workflowai.core.client.models import (
    CreateTaskRequest,
    CreateTaskResponse,
    RunRequest,
    TaskRunResponse,
)
from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_run import TaskRun
from workflowai.core.domain.task_version_reference import TaskVersionReference


class WorkflowAIClient:
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.api = APIClient(
            endpoint or os.getenv("WORKFLOWAI_ENDPOINT", "https://api.workflowai.ai"),
            api_key or os.getenv("WORKFLOWAI_API_KEY", ""),
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

    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        version: Optional[TaskVersionReference] = None,
        stream: bool = False,
        use_cache: CacheUsage = "when_available",
        labels: Optional[set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Union[TaskRun[TaskInput, TaskOutput], AsyncIterator[TaskOutput]]:
        if not task.id or not task.schema_id:
            await self.register(task)

        request = RunRequest(
            task_input=task_input.model_dump(),
            group=version or task.version,
            stream=stream,
            use_cache=use_cache,
            labels=labels,
            metadata=metadata,
        )

        route = f"/tasks/{task.id}/run"

        if not stream:
            res = await self.api.post(route, request, returns=TaskRunResponse)
            return res.to_domain(task)

        return self.api.stream(method="POST", path=route, returns=task.output_class)
