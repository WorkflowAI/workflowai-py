from pydantic import BaseModel, Field

from workflowai.core.domain.task_version_properties import TaskVersionProperties


class TaskVersion(BaseModel):
    properties: TaskVersionProperties = Field(
        default_factory=TaskVersionProperties,
        description="The properties used for executing the run.",
    )
