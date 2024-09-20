from typing import Optional

from pydantic import BaseModel, Field


class LLMUsage(BaseModel):
    """An object to store usage information for the LLM provider"""

    prompt_token_count: Optional[int] = Field(
        default=None, description="The number of tokens in the prompt",
    )
    prompt_cost_usd: Optional[float] = Field(
        default=None, description="The cost of the prompt in USD",
    )

    completion_token_count: Optional[int] = Field(
        default=None, description="The number of tokens in the completion",
    )
    completion_cost_usd: Optional[float] = Field(
        default=None, description="The cost of the completion in USD",
    )

    @property
    def cost_usd(self) -> Optional[float]:
        if self.prompt_cost_usd and self.completion_cost_usd:
            return self.prompt_cost_usd + self.completion_cost_usd

        # If either 'prompt_cost_usd' or 'completion_cost_usd' is missing, we consider there is a problem and prefer
        # to return nothing rather than a False value.
        return None
