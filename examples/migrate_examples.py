from typing import Callable, TypeVar

from pydantic import BaseModel

from workflowai import Client, Task
from workflowai.core.domain.task_example import TaskExample

_FromTaskInput = TypeVar("_FromTaskInput", bound=BaseModel)
_ToTaskInput = TypeVar("_ToTaskInput", bound=BaseModel)
_FromTaskOutput = TypeVar("_FromTaskOutput", bound=BaseModel)
_ToTaskOutput = TypeVar("_ToTaskOutput", bound=BaseModel)

Migrator = Callable[
    [_FromTaskInput, _FromTaskOutput], tuple[_ToTaskInput, _ToTaskOutput]
]


async def migrate_examples(
    client: Client,
    from_task: Task[_FromTaskInput, _FromTaskOutput],
    to_task: Task[_ToTaskInput, _ToTaskOutput],
    migrate_fn: Migrator[_FromTaskInput, _FromTaskOutput, _ToTaskInput, _ToTaskOutput],
):
    examples = await client.list_examples(from_task, limit=30)

    for example in examples.items:
        to_input, to_output = migrate_fn(example.task_input, example.task_output)
        await client.import_example(
            TaskExample(
                task=to_task,
                task_input=to_input,
                task_output=to_output,
            )
        )
