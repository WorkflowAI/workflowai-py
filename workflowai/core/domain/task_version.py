from pydantic import BaseModel, Field

from workflowai.core.domain.version_properties import VersionProperties


class TaskVersion(BaseModel):
    properties: VersionProperties = Field(
        default_factory=VersionProperties,
        description="The properties used for executing the run.",
    )
