from typing import Any, Optional, Union

from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict

from workflowai.core.client._types import OutputValidator
from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import AgentOutput
from workflowai.core.domain.version import Version as DVersion
from workflowai.core.domain.version_properties import VersionProperties as DVersionProperties


class RunRequest(BaseModel):
    task_input: dict[str, Any]

    version: Union[str, int, dict[str, Any]]

    use_cache: Optional[CacheUsage] = None

    metadata: Optional[dict[str, Any]] = None

    labels: Optional[set[str]] = None  # deprecated, to be included in metadata

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

    def to_domain(self, task_id: str, task_schema_id: int, validator: OutputValidator[AgentOutput]) -> Run[AgentOutput]:
        return Run(
            id=self.id,
            agent_id=task_id,
            schema_id=task_schema_id,
            output=validator(self.task_output),
            version=self.version
            and DVersion(
                properties=DVersionProperties.model_construct(
                    None,
                    **self.version.properties,
                ),
            ),
            duration_seconds=self.duration_seconds,
            cost_usd=self.cost_usd,
        )


class CreateAgentRequest(BaseModel):
    id: str = Field(description="The agent id, must be unique per tenant and URL safe")
    input_schema: dict[str, Any] = Field(description="The input schema for the agent")
    output_schema: dict[str, Any] = Field(description="The output schema for the agent")


class CreateAgentResponse(BaseModel):
    id: str
    schema_id: int
