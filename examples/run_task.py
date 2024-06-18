from asyncio import run as aiorun

import typer
from pydantic import BaseModel, Field
from rich import print as rprint

import workflowai
from workflowai import Task
from workflowai.core.domain.task_version_reference import TaskVersionReference


class CityToCapitalTaskInput(BaseModel):
    city: str = Field(
        description="The name of the city for which the capital is to be found",
        examples=["Tokyo"],
    )


class CityToCapitalTaskOutput(BaseModel):
    capital: str = Field(
        description="The capital of the specified city", examples=["Tokyo"]
    )


class CityToCapitalTask(Task[CityToCapitalTaskInput, CityToCapitalTaskOutput]):
    id: str = "citytocapital"
    schema_id: int = 1
    input_class: type[CityToCapitalTaskInput] = CityToCapitalTaskInput
    output_class: type[CityToCapitalTaskOutput] = CityToCapitalTaskOutput

    version: TaskVersionReference = TaskVersionReference(
        iteration=4,
    )


def main(city: str):
    client = workflowai.start()
    task = CityToCapitalTask()

    async def _inner():
        task_input = CityToCapitalTaskInput(city=city)
        task_run = await client.run(task, task_input)

        rprint(task_run.task_output)

    aiorun(_inner())


if __name__ == "__main__":
    typer.run(main)
