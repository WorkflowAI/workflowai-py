from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["USER", "ASSISTANT"] = Field(
        description="The role of the message sender",
        examples=["USER", "ASSISTANT"],
    )
    content: str = Field(
        description="The content of the message",
        examples=[
            "Thank you for your help!",
            "What is the weather forecast for tomorrow?",
        ],
    )


class UserChatMessage(ChatMessage):
    role: Literal["USER", "ASSISTANT"] = "USER"


class AssistantChatMessage(ChatMessage):
    role: Literal["USER", "ASSISTANT"] = "ASSISTANT"
