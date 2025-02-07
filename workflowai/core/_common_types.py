from typing import (
    Annotated,
    Any,
    Generic,
    Optional,
    Protocol,
    TypeVar,
)

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict

from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.task import AgentOutput
from workflowai.core.domain.version_reference import VersionReference

AgentInputContra = TypeVar("AgentInputContra", bound=BaseModel, contravariant=True)
AgentOutputCov = TypeVar("AgentOutputCov", bound=BaseModel, covariant=True)


class OutputValidator(Protocol, Generic[AgentOutputCov]):
    def __call__(self, data: dict[str, Any], has_tool_call_requests: bool) -> AgentOutputCov: ...


class VersionRunParams(TypedDict):
    model: NotRequired[Optional[str]]
    version: NotRequired[Optional["VersionReference"]]
    instructions: NotRequired[Optional[str]]
    temperature: NotRequired[Optional[float]]


class BaseRunParams(VersionRunParams):
    use_cache: NotRequired["CacheUsage"]
    metadata: NotRequired[Optional[dict[str, Any]]]
    labels: NotRequired[Optional[set[str]]]
    max_retry_delay: NotRequired[float]
    max_retry_count: NotRequired[float]

    max_tool_iterations: NotRequired[int]  # 10 by default


class RunParams(BaseRunParams, Generic[AgentOutput]):
    id: Annotated[
        NotRequired[str],
        "A user defined ID for the run. The ID must be a UUID7, ordered by creation time."
        "If not provided, a UUID7 will be assigned by the server",
    ]
    validator: NotRequired[OutputValidator["AgentOutput"]]
