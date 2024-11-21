from typing import Any, Optional, Union

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict

from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_run import Run, RunChunk
from workflowai.core.domain.task_version import TaskVersion
from workflowai.core.domain.task_version_properties import TaskVersionProperties


class RunRequest(BaseModel):
    task_input: dict[str, Any]

    version: Union[str, int]

    use_cache: Optional[CacheUsage] = None

    metadata: Optional[dict[str, Any]] = None

    private_fields: Optional[set[str]] = None

    stream: Optional[bool] = None


# Not using a base model to avoid validation
class VersionProperties(TypedDict):
    model: NotRequired[Optional[str]]
    provider: NotRequired[Optional[str]]
    temperature: NotRequired[Optional[float]]
    instructions: NotRequired[Optional[str]]


class Version(BaseModel):
    properties: VersionProperties


class RunResponse(BaseModel):
    id: str
    task_output: dict[str, Any]

    version: Version
    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None

    def to_domain(self, task: Task[TaskInput, TaskOutput]) -> Run[TaskOutput]:
        return Run(
            id=self.id,
            task_output=task.output_class.model_validate(self.task_output),
            version=TaskVersion(
                properties=TaskVersionProperties.model_construct(
                    None,
                    **self.version.properties,
                ),
            ),
            duration_seconds=self.duration_seconds,
            cost_usd=self.cost_usd,
        )


class RunStreamChunk(BaseModel):
    id: str
    task_output: dict[str, Any]

    version: Optional[Version] = None
    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None

    def to_domain(self, task: Task[TaskInput, TaskOutput]) -> Union[Run[TaskOutput], RunChunk[TaskOutput]]:
        if self.version is None:
            return RunChunk(
                id=self.id,
                task_output=task.output_class.model_validate(self.task_output),
            )

        return Run(
            id=self.id,
            task_output=task.output_class.model_validate(self.task_output),
            version=TaskVersion(
                properties=TaskVersionProperties.model_construct(
                    None,
                    **self.version.properties,
                ),
            ),
            duration_seconds=self.duration_seconds,
            cost_usd=self.cost_usd,
        )
