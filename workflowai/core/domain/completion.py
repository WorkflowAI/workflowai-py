from typing import Optional

from pydantic import BaseModel, Field


class CompletionUsage(BaseModel):
    """Usage information for a completion."""

    completion_token_count: Optional[int] = None
    completion_cost_usd: Optional[float] = None
    reasoning_token_count: Optional[int] = None
    prompt_token_count: Optional[int] = None
    prompt_token_count_cached: Optional[int] = None
    prompt_cost_usd: Optional[float] = None
    prompt_audio_token_count: Optional[int] = None
    prompt_audio_duration_seconds: Optional[float] = None
    prompt_image_count: Optional[int] = None
    model_context_window_size: Optional[int] = None


class Message(BaseModel):
    """A message in a completion."""

    role: str = ""
    content: str = ""


class Completion(BaseModel):
    """A completion from the model."""

    messages: list[Message] = Field(default_factory=list)
    response: Optional[str] = None
    usage: CompletionUsage = Field(default_factory=CompletionUsage)


class CompletionsResponse(BaseModel):
    """Response from the completions API endpoint."""

    completions: list[Completion]
