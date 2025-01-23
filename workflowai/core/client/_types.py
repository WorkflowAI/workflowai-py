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
from workflowai.core.domain.task import TaskInput, TaskOutput
from workflowai.core.domain.version_reference import VersionReference

TaskInputContra = TypeVar("TaskInputContra", bound=BaseModel, contravariant=True)
TaskOutputCov = TypeVar("TaskOutputCov", bound=BaseModel, covariant=True)

OutputValidator = Callable[[dict[str, Any]], TaskOutput]


class RunParams(TypedDict, Generic[TaskOutput]):
    version: NotRequired[Optional[VersionReference]]
    use_cache: NotRequired[CacheUsage]
    metadata: NotRequired[Optional[dict[str, Any]]]
    labels: NotRequired[Optional[set[str]]]
    max_retry_delay: NotRequired[float]
    max_retry_count: NotRequired[float]
    validator: NotRequired[OutputValidator[TaskOutput]]


class RunFn(Protocol, Generic[TaskInputContra, TaskOutput]):
    async def __call__(self, task_input: TaskInputContra) -> Run[TaskOutput]: ...


class RunFnOutputOnly(Protocol, Generic[TaskInputContra, TaskOutputCov]):
    async def __call__(self, task_input: TaskInputContra) -> TaskOutputCov: ...


class StreamRunFn(Protocol, Generic[TaskInputContra, TaskOutput]):
    def __call__(
        self,
        task_input: TaskInputContra,
    ) -> AsyncIterator[Run[TaskOutput]]: ...


class StreamRunFnOutputOnly(Protocol, Generic[TaskInputContra, TaskOutputCov]):
    def __call__(
        self,
        task_input: TaskInputContra,
    ) -> AsyncIterator[TaskOutputCov]: ...


RunTemplate = Union[
    RunFn[TaskInput, TaskOutput],
    RunFnOutputOnly[TaskInput, TaskOutput],
    StreamRunFn[TaskInput, TaskOutput],
    StreamRunFnOutputOnly[TaskInput, TaskOutput],
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


class FinalRunFn(_BaseProtocol, Protocol, Generic[TaskInputContra, TaskOutput]):
    async def __call__(
        self,
        task_input: TaskInputContra,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> Run[TaskOutput]: ...


class FinalRunFnOutputOnly(_BaseProtocol, Protocol, Generic[TaskInputContra, TaskOutput]):
    async def __call__(
        self,
        task_input: TaskInputContra,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> TaskOutput: ...


class FinalStreamRunFn(_BaseProtocol, Protocol, Generic[TaskInputContra, TaskOutput]):
    def __call__(
        self,
        task_input: TaskInputContra,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> AsyncIterator[Run[TaskOutput]]: ...


class FinalStreamRunFnOutputOnly(_BaseProtocol, Protocol, Generic[TaskInputContra, TaskOutputCov]):
    def __call__(
        self,
        task_input: TaskInputContra,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> AsyncIterator[TaskOutputCov]: ...


FinalRunTemplate = Union[
    FinalRunFn[TaskInput, TaskOutput],
    FinalRunFnOutputOnly[TaskInput, TaskOutput],
    FinalStreamRunFn[TaskInput, TaskOutput],
    FinalStreamRunFnOutputOnly[TaskInput, TaskOutput],
]


class TaskDecorator(Protocol):
    @overload
    def __call__(self, fn: RunFn[TaskInput, TaskOutput]) -> FinalRunFn[TaskInput, TaskOutput]: ...

    @overload
    def __call__(self, fn: RunFnOutputOnly[TaskInput, TaskOutput]) -> FinalRunFnOutputOnly[TaskInput, TaskOutput]: ...

    @overload
    def __call__(self, fn: StreamRunFn[TaskInput, TaskOutput]) -> FinalStreamRunFn[TaskInput, TaskOutput]: ...

    @overload
    def __call__(
        self,
        fn: StreamRunFnOutputOnly[TaskInput, TaskOutput],
    ) -> FinalStreamRunFnOutputOnly[TaskInput, TaskOutput]: ...

    def __call__(self, fn: RunTemplate[TaskInput, TaskOutput]) -> FinalRunTemplate[TaskInput, TaskOutput]: ...
