from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class TaskVersionProperties(BaseModel):
    """Properties that described a way a task run was executed.
    Although some keys are provided as an example, any key:value are accepted"""

    # Allow extra fields to support custom options
    model_config = ConfigDict(extra="allow")

    model: Optional[str] = Field(
        default=None, description="The LLM model used for the run",
    )
    provider: Optional[str] = Field(
        default=None, description="The LLM provider used for the run",
    )
    temperature: Optional[float] = Field(
        default=None, description="The temperature for generation",
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
        default=None, description="The name of the runner used",
    )

    runner_version: Optional[str] = Field(
        default=None, description="The version of the runner used",
    )

    few_shot: "Optional[FewShotConfiguration]" = Field(
        default=None, description="Few shot configuration",
    )


class FewShotConfiguration(BaseModel):
    count: Optional[int] = Field(
        default=None,
        description="The number of few-shot examples to use for the task",
    )

    selection: Union[Literal["latest", "manual"], str, None] = Field(
        default=None,
        description="The selection method to use for few-shot examples",
    )

    examples: Optional[list["FewShotExample"]] = Field(
        default=None,
        description="The few-shot examples used for the task. If provided, count and selection are ignored. "
        "If not provided, count and selection are used to select examples and the examples list will be set "
        "in the final group.",
    )


class FewShotExample(BaseModel):
    task_input: dict[str, Any]
    task_output: dict[str, Any]
