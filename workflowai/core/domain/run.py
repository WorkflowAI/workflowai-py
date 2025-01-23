import uuid
from typing import Any, Generic, Optional

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

from workflowai.core.domain.task import AgentOutput
from workflowai.core.domain.version import Version


class Run(BaseModel, Generic[AgentOutput]):
    """
    A run is an instance of a agent with a specific input and output.

    This class represent a run that already has been recorded and possibly
    been evaluated
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="The unique identifier of the run. This is a UUIDv7.",
    )
    agent_id: str
    schema_id: int
    output: AgentOutput

    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None

    version: Optional[Version] = Field(
        default=None,
        description="The version of the agent that was run. Only provided if the version differs from the version"
        " specified in the request, for example in case of a model fallback",
    )

    metadata: Optional[dict[str, Any]] = None
