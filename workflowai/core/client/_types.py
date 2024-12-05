from collections.abc import Callable
from typing import (
    Any,
    AsyncIterator,
    Generic,
    Literal,
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
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.version_reference import VersionReference

TaskInputContra = TypeVar("TaskInputContra", bound=BaseModel, contravariant=True)
TaskOutputCov = TypeVar("TaskOutputCov", bound=BaseModel, covariant=True)

OutputValidator = Callable[[dict[str, Any]], TaskOutput]


class RunParams(TypedDict, Generic[TaskOutput]):
    version: NotRequired[Optional[VersionReference]]
    use_cache: NotRequired[CacheUsage]
    metadata: NotRequired[Optional[dict[str, Any]]]
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


class Client(Protocol):
    """A client to interact with the WorkflowAI API"""

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: Literal[False] = False,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> Run[TaskOutput]: ...

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: Literal[True] = True,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> AsyncIterator[Run[TaskOutput]]: ...

    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: bool = False,
        **kwargs: Unpack[RunParams[TaskOutput]],
    ) -> Union[Run[TaskOutput], AsyncIterator[Run[TaskOutput]]]:
        """Run a task

        Args:
            task (Task[TaskInput, TaskOutput]): the task to run
            task_input (TaskInput): the input to the task
            version (Optional[TaskVersionReference], optional): the version of the task to run. If not provided,
                the version defined in the task is used. Defaults to None.
            environment (Optional[str], optional): the environment to run the task in. If not provided, the environment
                defined in the task is used. Defaults to None.
            iteration (Optional[int], optional): the iteration of the task to run. If not provided, the iteration
                defined in the task is used. Defaults to None.
            stream (bool, optional): whether to stream the output. If True, the function returns an async iterator of
                partial output objects. Defaults to False.
            use_cache (CacheUsage, optional): how to use the cache. Defaults to "when_available".
            labels (Optional[set[str]], optional): a set of labels to attach to the run.
                Labels are indexed and searchable. Defaults to None.
            metadata (Optional[dict[str, Any]], optional): a dictionary of metadata to attach to the run.
                Defaults to None.
            retry_delay (int, optional): The initial delay between retries in milliseconds. Defaults to 5000.
            max_retry_delay (int, optional): The maximum delay between retries in milliseconds. Defaults to 60000.
            max_retry_count (int, optional): The maximum number of retry attempts. Defaults to 1.

        Returns:
            Union[TaskRun[TaskInput, TaskOutput], AsyncIterator[TaskOutput]]: the task run object
                or an async iterator of output objects
        """
        ...

    def task(
        self,
        schema_id: int,
        task_id: Optional[str] = None,
        version: Optional[VersionReference] = None,
    ) -> TaskDecorator: ...
