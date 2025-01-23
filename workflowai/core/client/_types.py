from collections.abc import Callable
from typing import (
    Any,
    AsyncIterator,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    overload,
)

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict, Unpack

from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import AgentInput, AgentOutput
from workflowai.core.domain.version_reference import VersionReference

TaskInputContra = TypeVar("TaskInputContra", bound=BaseModel, contravariant=True)
TaskOutputCov = TypeVar("TaskOutputCov", bound=BaseModel, covariant=True)

OutputValidator = Callable[[dict[str, Any]], AgentOutput]


class RunParams(TypedDict, Generic[AgentOutput]):
    version: NotRequired[Optional[VersionReference]]
    use_cache: NotRequired[CacheUsage]
    metadata: NotRequired[Optional[dict[str, Any]]]
    labels: NotRequired[Optional[set[str]]]
    max_retry_delay: NotRequired[float]
    max_retry_count: NotRequired[float]
    validator: NotRequired[OutputValidator[AgentOutput]]


class RunFn(Protocol, Generic[TaskInputContra, AgentOutput]):
    async def __call__(self, task_input: TaskInputContra) -> Run[AgentOutput]: ...


class RunFnOutputOnly(Protocol, Generic[TaskInputContra, TaskOutputCov]):
    async def __call__(self, task_input: TaskInputContra) -> TaskOutputCov: ...


class StreamRunFn(Protocol, Generic[TaskInputContra, AgentOutput]):
    def __call__(
        self,
        task_input: TaskInputContra,
    ) -> AsyncIterator[Run[AgentOutput]]: ...


class StreamRunFnOutputOnly(Protocol, Generic[TaskInputContra, TaskOutputCov]):
    def __call__(
        self,
        task_input: TaskInputContra,
    ) -> AsyncIterator[TaskOutputCov]: ...


RunTemplate = Union[
    RunFn[AgentInput, AgentOutput],
    RunFnOutputOnly[AgentInput, AgentOutput],
    StreamRunFn[AgentInput, AgentOutput],
    StreamRunFnOutputOnly[AgentInput, AgentOutput],
]


class _BaseProtocol(Protocol):
    __name__: str
    __doc__: Optional[str]
    __module__: str
    __qualname__: str
    __annotations__: dict[str, Any]
    __defaults__: Optional[tuple[Any, ...]]
    __kwdefaults__: Optional[dict[str, Any]]
    __code__: Any


class FinalRunFn(_BaseProtocol, Protocol, Generic[TaskInputContra, AgentOutput]):
    async def __call__(
        self,
        task_input: TaskInputContra,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> Run[AgentOutput]: ...


class FinalRunFnOutputOnly(_BaseProtocol, Protocol, Generic[TaskInputContra, AgentOutput]):
    async def __call__(
        self,
        task_input: TaskInputContra,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> AgentOutput: ...


class FinalStreamRunFn(_BaseProtocol, Protocol, Generic[TaskInputContra, AgentOutput]):
    def __call__(
        self,
        task_input: TaskInputContra,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> AsyncIterator[Run[AgentOutput]]: ...


class FinalStreamRunFnOutputOnly(_BaseProtocol, Protocol, Generic[TaskInputContra, TaskOutputCov]):
    def __call__(
        self,
        task_input: TaskInputContra,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> AsyncIterator[TaskOutputCov]: ...


FinalRunTemplate = Union[
    FinalRunFn[AgentInput, AgentOutput],
    FinalRunFnOutputOnly[AgentInput, AgentOutput],
    FinalStreamRunFn[AgentInput, AgentOutput],
    FinalStreamRunFnOutputOnly[AgentInput, AgentOutput],
]


class TaskDecorator(Protocol):
    @overload
    def __call__(self, fn: RunFn[AgentInput, AgentOutput]) -> FinalRunFn[AgentInput, AgentOutput]: ...

    @overload
    def __call__(
        self,
        fn: RunFnOutputOnly[AgentInput, AgentOutput],
    ) -> FinalRunFnOutputOnly[AgentInput, AgentOutput]: ...

    @overload
    def __call__(self, fn: StreamRunFn[AgentInput, AgentOutput]) -> FinalStreamRunFn[AgentInput, AgentOutput]: ...

    @overload
    def __call__(
        self,
        fn: StreamRunFnOutputOnly[AgentInput, AgentOutput],
    ) -> FinalStreamRunFnOutputOnly[AgentInput, AgentOutput]: ...

    def __call__(self, fn: RunTemplate[AgentInput, AgentOutput]) -> FinalRunTemplate[AgentInput, AgentOutput]: ...
