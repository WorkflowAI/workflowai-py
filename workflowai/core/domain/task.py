from typing import TypeVar

from pydantic import BaseModel

TaskInput = TypeVar("TaskInput", bound=BaseModel)
TaskOutput = TypeVar("TaskOutput", bound=BaseModel)
