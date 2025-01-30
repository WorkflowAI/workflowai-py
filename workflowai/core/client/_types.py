from typing import (
    Any,
    AsyncIterator,
    Generic,
    Optional,
    Protocol,
    Union,
    overload,
)

from typing_extensions import Unpack

from workflowai.core._common_types import AgentInputContra, AgentOutputCov, RunParams
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import AgentInput, AgentOutput


class RunFn(Protocol, Generic[AgentInputContra, AgentOutput]):
    async def __call__(self, _: AgentInputContra, /) -> Run[AgentOutput]: ...


class RunFnOutputOnly(Protocol, Generic[AgentInputContra, AgentOutputCov]):
    async def __call__(self, _: AgentInputContra, /) -> AgentOutputCov: ...


class StreamRunFn(Protocol, Generic[AgentInputContra, AgentOutput]):
    def __call__(self, _: AgentInputContra, /) -> AsyncIterator[Run[AgentOutput]]: ...


class StreamRunFnOutputOnly(Protocol, Generic[AgentInputContra, AgentOutputCov]):
    def __call__(self, _: AgentInputContra, /) -> AsyncIterator[AgentOutputCov]: ...


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


class FinalRunFn(_BaseProtocol, Protocol, Generic[AgentInputContra, AgentOutput]):
    async def __call__(
        self,
        _: AgentInputContra,
        /,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> Run[AgentOutput]: ...


class FinalRunFnOutputOnly(_BaseProtocol, Protocol, Generic[AgentInputContra, AgentOutput]):
    async def __call__(
        self,
        _: AgentInputContra,
        /,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> AgentOutput: ...


class FinalStreamRunFn(_BaseProtocol, Protocol, Generic[AgentInputContra, AgentOutput]):
    def __call__(
        self,
        _: AgentInputContra,
        /,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> AsyncIterator[Run[AgentOutput]]: ...


class FinalStreamRunFnOutputOnly(_BaseProtocol, Protocol, Generic[AgentInputContra, AgentOutputCov]):
    def __call__(
        self,
        _: AgentInputContra,
        /,
        **kwargs: Unpack[RunParams[AgentOutput]],
    ) -> AsyncIterator[AgentOutputCov]: ...


FinalRunTemplate = Union[
    FinalRunFn[AgentInput, AgentOutput],
    FinalRunFnOutputOnly[AgentInput, AgentOutput],
    FinalStreamRunFn[AgentInput, AgentOutput],
    FinalStreamRunFnOutputOnly[AgentInput, AgentOutput],
]


class AgentDecorator(Protocol):
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
