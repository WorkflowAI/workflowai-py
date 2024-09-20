from typing import Any, Optional

from pydantic import BaseModel, Field

from workflowai.core.domain.llm_usage import LLMUsage


class LLMCompletion(BaseModel):
    """A raw response from the LLM api"""

    messages: list[dict[str, Any]] = Field(
        description="The raw messages sent to the LLM",
    )
    response: Optional[str] = Field(
        default=None, description="The raw response from the LLM",
    )

    usage: Optional[LLMUsage] = Field(
        default=None, description="The usage of the LLM model",
    )
