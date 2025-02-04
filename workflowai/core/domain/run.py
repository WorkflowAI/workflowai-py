import uuid
from collections.abc import Iterable
from typing import Any, Generic, Optional, Protocol

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]
from typing_extensions import Unpack

from workflowai.core import _common_types
from workflowai.core.client import _types
from workflowai.core.domain.errors import BaseError
from workflowai.core.domain.task import AgentOutput
from workflowai.core.domain.tool_call import ToolCall, ToolCallRequest, ToolCallResult
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

    tool_calls: Optional[list[ToolCall]] = None
    tool_call_requests: Optional[list[ToolCallRequest]] = None

    error: Optional[BaseError] = Field(
        default=None,
        description="An error that occurred during the run. Only provided if the run failed.",
    )

    _agent: Optional["_AgentBase[AgentOutput]"] = None

    def __eq__(self, other: object) -> bool:
        # Probably over simplistic but the object is not crazy complicated
        # We just need a way to ignore the agent object
        if not isinstance(other, Run):
            return False
        if self.__dict__ == other.__dict__:
            return True
        # Otherwise we check without the agent
        for field, value in self.__dict__.items():
            if field == "_agent":
                continue
            if not value == other.__dict__.get(field):
                return False
        return True

    async def reply(
        self,
        user_message: Optional[str] = None,
        tool_results: Optional[Iterable[ToolCallResult]] = None,
        **kwargs: Unpack["_common_types.RunParams[AgentOutput]"],
    ):
        if not self._agent:
            raise ValueError("Agent is not set")
        return await self._agent.reply(
            run_id=self.id,
            user_message=user_message,
            tool_results=tool_results,
            **kwargs,
        )

    @property
    def model(self):
        if self.version is None:
            return None
        return self.version.properties.model


class _AgentBase(Protocol, Generic[AgentOutput]):
    async def reply(
        self,
        run_id: str,
        user_message: Optional[str] = None,
        tool_results: Optional[Iterable[ToolCallResult]] = None,
        **kwargs: Unpack["_types.RunParams[AgentOutput]"],
    ) -> "Run[AgentOutput]":
        """Reply to a run. Either a user_message or tool_results must be provided."""
        ...
