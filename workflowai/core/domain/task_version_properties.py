from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskVersionProperties(BaseModel):
    """Properties that described a way a task run was executed.
    Although some keys are provided as an example, any key:value are accepted"""

    # Allow extra fields to support custom options
    model_config = ConfigDict(extra="allow")

    model: Optional[str] = Field(
        default=None,
        description="The LLM model used for the run",
    )
    provider: Optional[str] = Field(
        default=None,
        description="The LLM provider used for the run",
    )
    temperature: Optional[float] = Field(
        default=None,
        description="The temperature for generation",
    )
    instructions: Optional[str] = Field(
        default=None,
        description="The instructions passed to the runner in order to generate the prompt.",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="The maximum tokens to generate in the prompt",
    )

    runner_name: Optional[str] = Field(
        default=None,
        description="The name of the runner used",
    )

    runner_version: Optional[str] = Field(
        default=None,
        description="The version of the runner used",
    )
