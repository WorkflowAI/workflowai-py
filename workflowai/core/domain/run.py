import uuid
from typing import Any, Generic, Optional

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

from workflowai.core.domain.task import TaskOutput
from workflowai.core.domain.task_version import TaskVersion


class Run(BaseModel, Generic[TaskOutput]):
    """
    A task run is an instance of a task with a specific input and output.

    This class represent a task run that already has been recorded and possibly
    been evaluated
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="The unique identifier of the task run. This is a UUIDv7.",
    )
    task_id: str
    task_schema_id: int
    task_output: TaskOutput

    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None

    version: Optional[TaskVersion] = Field(
        default=None,
        description="The version of the task that was run. Only provided if the version differs from the version"
        " specified in the request, for example in case of a model fallback",
    )

    metadata: Optional[dict[str, Any]] = None
