from typing import TypeVar

from pydantic import BaseModel

AgentInput = TypeVar("AgentInput", bound=BaseModel)
AgentOutput = TypeVar("AgentOutput", bound=BaseModel)
