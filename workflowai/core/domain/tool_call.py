from typing import Any, Literal, Optional

from pydantic import BaseModel


class ToolCall(BaseModel):
    """A tool call that has already been executed, either by workflowai or by the user"""

    id: str
    name: str
    input_preview: str
    output_preview: Optional[str]
    error: Optional[str]
    status: Optional[Literal["success", "failed", "in_progress"]]


class ToolCallRequest(BaseModel):
    """A request to execute a tool call"""

    id: str
    name: str
    input: dict[str, Any]


class ToolCallResult(BaseModel):
    """The output of a tool call"""

    id: str
    output: Optional[Any] = None
    error: Optional[str] = None
