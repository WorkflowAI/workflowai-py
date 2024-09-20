from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from workflowai.core.domain.task_version import TaskVersion
from workflowai.core.domain.task_version_properties import TaskVersionProperties


class TaskVersionReference(BaseModel):
    """Refer to an existing group or create a new one with the given properties.
    Only one of id, iteration or properties must be provided"""

    id: Optional[str] = Field(description="The id of an existing group", default=None)
    iteration: Optional[int] = Field(
        description="An iteration for an existing group.", default=None,
    )
    properties: Optional[TaskVersionProperties] = Field(
        description="The properties to evaluate the task schema with. A group will be created if needed",
        default=None,
    )
    alias: Optional[str] = Field(description="An alias for the group", default=None)

    is_external: Optional[bool] = Field(
        description="Whether the group is external, i-e not created by internal runners",
        default=None,
    )

    @model_validator(mode="after")
    def post_validate(self) -> Self:
        count = sum(
            1
            for x in [
                self.id,
                self.iteration,
                self.properties,
                self.alias,
            ]
            if x
        )
        if count != 1:
            raise ValueError(
                "Exactly one of id, iteration or properties must be provided",
            )
        return self

    @classmethod
    def with_properties(
        cls,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        instructions: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> "TaskVersionReference":
        """Short hand for creating a TaskVersionReference with properties."""
        return TaskVersionReference(
            properties=TaskVersionProperties(
                model=model,
                provider=provider,
                temperature=temperature,
                instructions=instructions,
                max_tokens=max_tokens,
                **kwargs,
            ),
        )

    @classmethod
    def from_version(cls, version: TaskVersion):
        if version.iteration:
            return cls(iteration=version.iteration)
        if version.id:
            return cls(id=version.id)
        if version.aliases:
            return cls(alias=next(iter(version.aliases)))
        return cls(properties=version.properties)
