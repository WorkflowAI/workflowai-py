from datetime import datetime
from typing import Generic

from pydantic import BaseModel, Field

from workflowai.core.domain.task import Task, TaskInput, TaskOutput


class TaskExample(BaseModel, Generic[TaskInput, TaskOutput]):
    id: str = Field(default="", description="A unique identifier")
    created_at: datetime = Field(
        default_factory=datetime.now, description="The creation date"
    )

    task: Task[TaskInput, TaskOutput]

    task_input: TaskInput
    task_output: TaskOutput
