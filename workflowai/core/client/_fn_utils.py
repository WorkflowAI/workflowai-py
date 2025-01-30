import functools
import inspect
from collections.abc import Callable, Iterable
from typing import (
    Any,
    AsyncIterator,
    Generic,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel
from typing_extensions import Unpack

from workflowai.core.client._api import APIClient
from workflowai.core.client._types import (
    AgentDecorator,
    FinalRunTemplate,
    RunParams,
    RunTemplate,
)
from workflowai.core.client.agent import Agent
from workflowai.core.domain.model import ModelOrStr
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import AgentInput, AgentOutput
from workflowai.core.domain.version_properties import VersionProperties
from workflowai.core.domain.version_reference import VersionReference

# TODO: add sync support


def get_generic_args(t: type[BaseModel]) -> Union[Sequence[type], None]:
    return t.__pydantic_generic_metadata__.get("args")


def check_return_type(return_type_hint: Type[Any]) -> tuple[bool, Type[BaseModel]]:
    if issubclass(return_type_hint, Run):
        args = get_generic_args(return_type_hint)  # pyright: ignore [reportUnknownArgumentType]
        if not args:
            raise ValueError("Run must have a generic argument")
        output_cls = args[0]
        if not issubclass(output_cls, BaseModel):
            raise ValueError("Run generic argument must be a subclass of BaseModel")
        return False, output_cls
    if issubclass(return_type_hint, BaseModel):
        return True, return_type_hint
    raise ValueError("Function must have a return type hint that is a subclass of Pydantic's 'BaseModel' or 'Run'")


class RunFunctionSpec(NamedTuple):
    stream: bool
    output_only: bool
    input_cls: Type[BaseModel]
    output_cls: Type[BaseModel]


def is_async_iterator(t: type[Any]) -> bool:
    ori: Any = get_origin(t)
    if not ori:
        return False
    return issubclass(ori, AsyncIterator)


def _first_arg_name(fn: Callable[..., Any]) -> Optional[str]:
    sig = inspect.signature(fn)
    for param in sig.parameters.values():
        if param.kind == param.POSITIONAL_OR_KEYWORD:
            return param.name
    return None


def extract_fn_spec(fn: RunTemplate[AgentInput, AgentOutput]) -> RunFunctionSpec:
    first_arg_name = _first_arg_name(fn)
    if not first_arg_name:
        raise ValueError("Function must have a first positional argument")
    hints = get_type_hints(fn)
    if "return" not in hints:
        raise ValueError("Function must have a return type hint")
    if first_arg_name not in hints:
        raise ValueError("Function must have a first positional parameter")

    return_type_hint = hints["return"]
    input_cls = hints[first_arg_name]
    if not issubclass(input_cls, BaseModel):
        raise ValueError("First positional parameter must be a subclass of BaseModel")

    output_cls = None

    if is_async_iterator(return_type_hint):
        stream = True
        output_only, output_cls = check_return_type(get_args(return_type_hint)[0])
    else:
        stream = False
        output_only, output_cls = check_return_type(return_type_hint)

    return RunFunctionSpec(stream, output_only, input_cls, output_cls)


class _RunnableAgent(Agent[AgentInput, AgentOutput], Generic[AgentInput, AgentOutput]):
    async def __call__(self, input: AgentInput, **kwargs: Unpack[RunParams[AgentOutput]]):  # noqa: A002
        return await self.run(input, **kwargs)


class _RunnableOutputOnlyAgent(Agent[AgentInput, AgentOutput], Generic[AgentInput, AgentOutput]):
    async def __call__(self, input: AgentInput, **kwargs: Unpack[RunParams[AgentOutput]]):  # noqa: A002
        return (await self.run(input, **kwargs)).output


class _RunnableStreamAgent(Agent[AgentInput, AgentOutput], Generic[AgentInput, AgentOutput]):
    def __call__(self, input: AgentInput, **kwargs: Unpack[RunParams[AgentOutput]]):  # noqa: A002
        return self.stream(input, **kwargs)


class _RunnableStreamOutputOnlyAgent(Agent[AgentInput, AgentOutput], Generic[AgentInput, AgentOutput]):
    async def __call__(self, input: AgentInput, **kwargs: Unpack[RunParams[AgentOutput]]):  # noqa: A002
        async for chunk in self.stream(input, **kwargs):
            yield chunk.output


def wrap_run_template(
    client: Callable[[], APIClient],
    agent_id: str,
    schema_id: Optional[int],
    version: Optional[VersionReference],
    model: Optional[ModelOrStr],
    fn: RunTemplate[AgentInput, AgentOutput],
    tools: Optional[Iterable[Callable[..., Any]]] = None,
) -> Union[
    _RunnableAgent[AgentInput, AgentOutput],
    _RunnableOutputOnlyAgent[AgentInput, AgentOutput],
    _RunnableStreamAgent[AgentInput, AgentOutput],
    _RunnableStreamOutputOnlyAgent[AgentInput, AgentOutput],
]:
    stream, output_only, input_cls, output_cls = extract_fn_spec(fn)

    if not version and (fn.__doc__ or model):
        version = VersionProperties(
            instructions=fn.__doc__,
            model=model,
        )

    if stream:
        task_cls = _RunnableStreamOutputOnlyAgent if output_only else _RunnableStreamAgent
    else:
        task_cls = _RunnableOutputOnlyAgent if output_only else _RunnableAgent
    return task_cls(  # pyright: ignore [reportUnknownVariableType]
        agent_id=agent_id,
        input_cls=input_cls,
        output_cls=output_cls,
        api=client,
        schema_id=schema_id,
        version=version,
        tools=tools,
    )


def agent_id_from_fn_name(fn: Any) -> str:
    return fn.__name__.replace("_", "-").lower()


def agent_wrapper(
    client: Callable[[], APIClient],
    schema_id: Optional[int] = None,
    agent_id: Optional[str] = None,
    version: Optional[VersionReference] = None,
    model: Optional[ModelOrStr] = None,
    tools: Optional[Iterable[Callable[..., Any]]] = None,
) -> AgentDecorator:
    def wrap(fn: RunTemplate[AgentInput, AgentOutput]) -> FinalRunTemplate[AgentInput, AgentOutput]:
        tid = agent_id or agent_id_from_fn_name(fn)
        return functools.wraps(fn)(wrap_run_template(client, tid, schema_id, version, model, fn, tools))  # pyright: ignore [reportReturnType]

    # pyright is unhappy with generics
    return wrap  # pyright: ignore [reportReturnType]
