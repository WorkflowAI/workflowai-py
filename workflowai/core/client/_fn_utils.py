import functools
from collections.abc import Callable
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
    FinalRunTemplate,
    RunParams,
    RunTemplate,
    TaskDecorator,
)
from workflowai.core.client.agent import Agent
from workflowai.core.domain.model import Model
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import TaskInput, TaskOutput
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


def extract_fn_spec(fn: RunTemplate[TaskInput, TaskOutput]) -> RunFunctionSpec:
    hints = get_type_hints(fn)
    if "return" not in hints:
        raise ValueError("Function must have a return type hint")
    if "task_input" not in hints:
        raise ValueError("Function must have a task_input parameter")

    return_type_hint = hints["return"]
    input_cls = hints["task_input"]
    if not issubclass(input_cls, BaseModel):
        raise ValueError("task_input must be a subclass of BaseModel")

    output_cls = None

    if is_async_iterator(return_type_hint):
        stream = True
        output_only, output_cls = check_return_type(get_args(return_type_hint)[0])
    else:
        stream = False
        output_only, output_cls = check_return_type(return_type_hint)

    return RunFunctionSpec(stream, output_only, input_cls, output_cls)


class _RunnableAgent(Agent[TaskInput, TaskOutput], Generic[TaskInput, TaskOutput]):
    async def __call__(self, task_input: TaskInput, **kwargs: Unpack[RunParams[TaskOutput]]):
        return await self.run(task_input, **kwargs)


class _RunnableOutputOnlyAgent(Agent[TaskInput, TaskOutput], Generic[TaskInput, TaskOutput]):
    async def __call__(self, task_input: TaskInput, **kwargs: Unpack[RunParams[TaskOutput]]):
        return (await self.run(task_input, **kwargs)).task_output


class _RunnableStreamAgent(Agent[TaskInput, TaskOutput], Generic[TaskInput, TaskOutput]):
    def __call__(self, task_input: TaskInput, **kwargs: Unpack[RunParams[TaskOutput]]):
        return self.stream(task_input, **kwargs)


class _RunnableStreamOutputOnlyAgent(Agent[TaskInput, TaskOutput], Generic[TaskInput, TaskOutput]):
    async def __call__(self, task_input: TaskInput, **kwargs: Unpack[RunParams[TaskOutput]]):
        async for chunk in self.stream(task_input, **kwargs):
            yield chunk.task_output


def wrap_run_template(
    client: Callable[[], APIClient],
    agent_id: str,
    schema_id: Optional[int],
    version: Optional[VersionReference],
    model: Optional[Model],
    fn: RunTemplate[TaskInput, TaskOutput],
) -> Union[
    _RunnableAgent[TaskInput, TaskOutput],
    _RunnableOutputOnlyAgent[TaskInput, TaskOutput],
    _RunnableStreamAgent[TaskInput, TaskOutput],
    _RunnableStreamOutputOnlyAgent[TaskInput, TaskOutput],
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
    )


def agent_id_from_fn_name(fn: Any) -> str:
    return fn.__name__.replace("_", "-").lower()


def agent_wrapper(
    client: Callable[[], APIClient],
    schema_id: Optional[int] = None,
    agent_id: Optional[str] = None,
    version: Optional[VersionReference] = None,
    model: Optional[Model] = None,
) -> TaskDecorator:
    def wrap(fn: RunTemplate[TaskInput, TaskOutput]) -> FinalRunTemplate[TaskInput, TaskOutput]:
        tid = agent_id or agent_id_from_fn_name(fn)
        return functools.wraps(fn)(wrap_run_template(client, tid, schema_id, version, model, fn))  # pyright: ignore [reportReturnType]

    # pyright is unhappy with generics
    return wrap  # pyright: ignore [reportReturnType]
