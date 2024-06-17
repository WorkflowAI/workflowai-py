from typing import Any, Optional

from pydantic import BaseModel

from workflowai.core.domain.llm_usage import LLMUsage


class LLMCompletion(BaseModel):
    messages: list[dict[str, Any]]
    response: Optional[str] = None

    usage: Optional[LLMUsage] = None
