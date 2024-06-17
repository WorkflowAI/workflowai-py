from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.llm_completion import LLMCompletion
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_evaluation import TaskEvaluation
from workflowai.core.domain.task_run import TaskRun
from workflowai.core.domain.task_version import TaskVersion
from workflowai.core.domain.task_version_reference import TaskVersionReference


class CreateTaskRequest(BaseModel):
    name: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    task_id: Optional[str] = None


class CreateTaskResponse(BaseModel):
    task_id: str = Field(description="the task id, stable accross all versions")
    task_schema_id: int = Field(
        description="""The task schema idx. The schema index only changes when the types
        of the input / ouput objects change so all task versions with the same schema idx
        have compatible input / output objects. Read only""",
    )
    name: str = Field(description="the task display name")

    class VersionedSchema(BaseModel):
        version: str
        json_schema: dict[str, Any]

    input_schema: VersionedSchema
    output_schema: VersionedSchema

    created_at: datetime


class RunRequest(BaseModel):
    task_input: dict[str, Any]

    group: TaskVersionReference

    id: Optional[str] = None

    stream: bool = False

    use_cache: Optional[CacheUsage]

    labels: Optional[set[str]]

    metadata: Optional[dict[str, Any]]


class TaskRunResponse(BaseModel):
    id: str
    task_id: str
    task_schema_id: int
    task_input: dict[str, Any]
    task_output: dict[str, Any]
    group: TaskVersion

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None
    created_at: datetime
    example_id: Optional[str]
    scores: Optional[list[TaskEvaluation]] = None
    labels: Optional[set[str]] = None
    metadata: Optional[dict[str, Any]] = None
    llm_completions: Optional[list[LLMCompletion]] = None

    def to_domain(self, task: Task[TaskInput, TaskOutput]):
        return TaskRun[TaskInput, TaskOutput](
            id=self.id,
            task=task,
            task_input=task.input_class.model_validate(self.task_input),
            task_output=task.output_class.model_validate(self.task_output),
            version=self.group,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_seconds=self.duration_seconds,
            cost_usd=self.cost_usd,
            created_at=self.created_at,
            example_id=self.example_id,
            scores=self.scores,
            labels=self.labels,
            metadata=self.metadata,
            llm_completions=self.llm_completions,
        )
