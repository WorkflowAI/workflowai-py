from typing import Optional

from pydantic import BaseModel


class LLMUsage(BaseModel):
    prompt_token_count: Optional[int] = None
    prompt_cost_usd: Optional[float] = None

    completion_token_count: Optional[int] = None
    completion_cost_usd: Optional[float] = None

    @property
    def cost_usd(self) -> Optional[float]:
        if self.prompt_cost_usd and self.completion_cost_usd:
            return self.prompt_cost_usd + self.completion_cost_usd

        # If either 'prompt_cost_usd' or 'completion_cost_usd' is missing, we consider there is a problem and prefer
        # to return nothing rather than a False value.
        return None
