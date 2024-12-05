from typing import Any, Optional, Union

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict

from workflowai.core.client._types import OutputValidator
from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import TaskOutput
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

    version: Optional[Version] = None
    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None

    def to_domain(self, task_id: str, task_schema_id: int, validator: OutputValidator[TaskOutput]) -> Run[TaskOutput]:
        return Run(
            id=self.id,
            task_id=task_id,
            task_schema_id=task_schema_id,
            task_output=validator(self.task_output),
            version=self.version
            and TaskVersion(
                properties=TaskVersionProperties.model_construct(
                    None,
                    **self.version.properties,
                ),
            ),
            duration_seconds=self.duration_seconds,
            cost_usd=self.cost_usd,
        )
