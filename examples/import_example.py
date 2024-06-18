from asyncio import run as aiorun

import typer
from rich import print as rprint

import workflowai
from examples.city_to_capital_task import (
    CityToCapitalTask,
    CityToCapitalTaskInput,
    CityToCapitalTaskOutput,
)
from workflowai import TaskExample


def main(city: str, capital: str):
    client = workflowai.start()
    task = CityToCapitalTask()

    async def _inner():
        task_example = TaskExample(
            task=task,
            task_input=CityToCapitalTaskInput(city=city),
            task_output=CityToCapitalTaskOutput(capital=capital),
        )
        imported = await client.import_example(task_example)

        rprint(imported)

    aiorun(_inner())


if __name__ == "__main__":
    typer.run(main)
