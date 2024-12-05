import functools
from collections.abc import Callable
from typing import (
    Any,
    AsyncIterator,
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

from workflowai.core.client._types import (
    Client,
    FinalRunFn,
    FinalRunFnOutputOnly,
    FinalRunTemplate,
    FinalStreamRunFn,
    FinalStreamRunFnOutputOnly,
    RunParams,
    RunTemplate,
    TaskDecorator,
)
from workflowai.core.domain.run import Run
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
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


class ExtractFnData(NamedTuple):
    stream: bool
    output_only: bool
    input_cls: Type[BaseModel]
    output_cls: Type[BaseModel]


def is_async_iterator(t: type[Any]) -> bool:
    ori: Any = get_origin(t)
    if not ori:
        return False
    return issubclass(ori, AsyncIterator)


def extract_fn_data(fn: RunTemplate[TaskInput, TaskOutput]) -> ExtractFnData:
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

    return ExtractFnData(stream, output_only, input_cls, output_cls)


def _wrap_run(client: Callable[[], Client], task: Task[TaskInput, TaskOutput]) -> FinalRunFn[TaskInput, TaskOutput]:
    async def wrap(task_input: TaskInput, **kwargs: Unpack[RunParams[TaskOutput]]) -> Run[TaskOutput]:
        return await client().run(task, task_input, stream=False, **kwargs)

    return wrap


def _wrap_run_output_only(
    client: Callable[[], Client],
    task: Task[TaskInput, TaskOutput],
) -> FinalRunFnOutputOnly[TaskInput, TaskOutput]:
    async def wrap(task_input: TaskInput, **kwargs: Unpack[RunParams[TaskOutput]]) -> TaskOutput:
        run = await client().run(task, task_input, stream=False, **kwargs)
        return run.task_output

    return wrap


def _wrap_stream_run(
    client: Callable[[], Client],
    task: Task[TaskInput, TaskOutput],
) -> FinalStreamRunFn[TaskInput, TaskOutput]:
    async def wrap(task_input: TaskInput, **kwargs: Unpack[RunParams[TaskOutput]]) -> AsyncIterator[Run[TaskOutput]]:
        s = await client().run(task, task_input, stream=True, **kwargs)
        async for chunk in s:
            yield chunk

    return wrap


def _wrap_stream_run_output_only(
    client: Callable[[], Client],
    task: Task[TaskInput, TaskOutput],
) -> FinalStreamRunFnOutputOnly[TaskInput, TaskOutput]:
    async def wrap(task_input: TaskInput, **kwargs: Unpack[RunParams[TaskOutput]]) -> AsyncIterator[TaskOutput]:
        s = await client().run(task, task_input, stream=True, **kwargs)
        async for chunk in s:
            yield chunk.task_output

    # TODO: not sure what's going on here...
    return wrap  # pyright: ignore [reportReturnType]


def wrap_run_template(
    client: Callable[[], Client],
    task_id: str,
    task_schema_id: int,
    version: Optional[VersionReference],
    fn: RunTemplate[TaskInput, TaskOutput],
):
    stream, output_only, input_cls, output_cls = extract_fn_data(fn)
    # There is some co / contravariant issue here...
    task: Task[TaskInput, TaskOutput] = Task(  # pyright: ignore [reportAssignmentType]
        id=task_id,
        schema_id=task_schema_id,
        input_class=input_cls,
        output_class=output_cls,
        version=version,
    )

    if stream:
        if output_only:
            return _wrap_stream_run_output_only(client, task)
        return _wrap_stream_run(client, task)
    if output_only:
        return _wrap_run_output_only(client, task)
    return _wrap_run(client, task)


def task_id_from_fn_name(fn: Any) -> str:
    return fn.__name__.replace("_", "-").lower()


def task_wrapper(
    client: Callable[[], Client],
    schema_id: int,
    task_id: Optional[str] = None,
    version: Optional[VersionReference] = None,
) -> TaskDecorator:
    def wrap(fn: RunTemplate[TaskInput, TaskOutput]) -> FinalRunTemplate[TaskInput, TaskOutput]:
        tid = task_id or task_id_from_fn_name(fn)
        return functools.wraps(fn)(wrap_run_template(client, tid, schema_id, version, fn))  # pyright: ignore [reportReturnType]

    # TODO: pyright is unhappy with generics
    return wrap  # pyright: ignore [reportReturnType]
