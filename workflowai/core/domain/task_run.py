import uuid
from typing import Any, Generic, Optional

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

from workflowai.core.domain.task import TaskOutput
from workflowai.core.domain.task_version import TaskVersion


class RunChunk(BaseModel, Generic[TaskOutput]):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="The unique identifier of the task run",
    )
    task_output: TaskOutput


class Run(RunChunk[TaskOutput]):
    """
    A task run is an instance of a task with a specific input and output.

    This class represent a task run that already has been recorded and possibly
    been evaluated
    """

    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None

    version: TaskVersion

    metadata: Optional[dict[str, Any]] = None
