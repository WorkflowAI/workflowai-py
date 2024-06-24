from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.llm_completion import LLMCompletion
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_evaluation import TaskEvaluation
from workflowai.core.domain.task_example import TaskExample
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


class _RunRequestCommon(BaseModel):
    task_input: dict[str, Any]

    group: TaskVersionReference

    id: Optional[str] = None

    labels: Optional[set[str]]

    metadata: Optional[dict[str, Any]]


class RunRequest(_RunRequestCommon):
    stream: bool = False

    use_cache: Optional[CacheUsage]


class ImportRunRequest(_RunRequestCommon):
    task_output: dict[str, Any]
    llm_completions: Optional[list[LLMCompletion]] = None
    cost_usd: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @classmethod
    def from_domain(cls, task_run: TaskRun[TaskInput, TaskOutput]):
        return cls(
            id=task_run.id,
            task_input=task_run.task_input.model_dump(mode="json"),
            task_output=task_run.task_output.model_dump(mode="json"),
            group=TaskVersionReference.from_version(task_run.version),
            labels=task_run.labels,
            metadata=task_run.metadata,
            llm_completions=task_run.llm_completions,
            cost_usd=task_run.cost_usd,
            start_time=task_run.start_time,
            end_time=task_run.end_time,
        )


class RunTaskStreamChunk(BaseModel):
    run_id: str
    task_output: dict[str, Any]


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


class ImportExampleRequest(BaseModel):
    task_input: dict[str, Any]
    task_output: dict[str, Any]

    @classmethod
    def from_domain(cls, task_example: TaskExample[TaskInput, TaskOutput]):
        return cls(
            task_input=task_example.task_input.model_dump(mode="json"),
            task_output=task_example.task_output.model_dump(mode="json"),
        )


class ExampleResponse(BaseModel):
    id: str
    task_input: dict[str, Any]
    task_output: dict[str, Any]

    def to_domain(self, task: Task[TaskInput, TaskOutput]):
        return TaskExample[TaskInput, TaskOutput](
            id=self.id,
            task=task,
            task_input=task.input_class.model_validate(self.task_input),
            task_output=task.output_class.model_validate(self.task_output),
        )


class PatchGroupRequest(BaseModel):
    add_alias: Optional[str] = Field(
        default=None,
        description="A new alias for the group. If the alias is already used in another group of the task schema"
        "it will be removed from the other group.",
    )

    remove_alias: Optional[str] = Field(
        default=None,
        description="An alias to remove from the group. The request is a noop if the group does not have the alias",
    )

    @model_validator(mode="after")
    def post_validate(self):
        if not self.add_alias and not self.remove_alias:
            raise ValueError("At least one of add_alias or remove_alias must be set")
        if self.add_alias == self.remove_alias:
            raise ValueError("Cannot add and remove the same alias")
        return self
