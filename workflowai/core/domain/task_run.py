import uuid
from datetime import datetime
from typing import Any, Generic, Optional

from pydantic import BaseModel, Field

from workflowai.core.domain.llm_completion import LLMCompletion
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_evaluation import TaskEvaluation
from workflowai.core.domain.task_version import TaskVersion


class TaskRun(BaseModel, Generic[TaskInput, TaskOutput]):
    """
    A task run is an instance of a task with a specific input and output.

    This class represent a task run that already has been recorded and possibly
    been evaluated
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="The unique identifier of the task run",
    )
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None

    task: Task[TaskInput, TaskOutput]

    task_input: TaskInput

    task_output: TaskOutput

    version: TaskVersion

    from_cache: bool = Field(
        default=False, description="Whether the task run was loaded from the cache",
    )

    # if available, the id of an example that match the task run input
    example_id: Optional[str] = None

    scores: Optional[list[TaskEvaluation]] = Field(
        default=None,
        description="A list of scores computed for the task run. A run can be evaluated in multiple ways.",
    )

    labels: Optional[set[str]] = Field(
        default=None,
        description="A list of labels ",
    )

    metadata: Optional[dict[str, Any]] = None

    llm_completions: Optional[list[LLMCompletion]] = Field(
        default=None,
        description="A list of raw completions used to generate the task output",
    )

    created_at: Optional[datetime] = None
