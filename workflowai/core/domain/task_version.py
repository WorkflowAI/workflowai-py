from typing import Optional

from pydantic import BaseModel, Field

from workflowai.core.domain.task_version_properties import TaskVersionProperties


class TaskVersion(BaseModel):
    id: str = Field(
        default="",
        description="The group id either client provided or generated, stable for given set of properties",
    )
    iteration: int = Field(
        default=0,
        description="The iteration of the group, incremented for each new group",
    )
    properties: TaskVersionProperties = Field(
        default_factory=TaskVersionProperties,
        description="The properties used for executing the run.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="A list of tags associated with the group. When empty, tags are computed from the properties.",
    )

    aliases: Optional[set[str]] = Field(
        default=None,
        description="A list of aliases to use in place of iteration or id. "
        "An alias can be used to uniquely identify a group for a given task. ",
    )

    is_external: Optional[bool] = Field(
        default=None,
        description="Whether the group is external, i-e not creating by internal runners",
    )
