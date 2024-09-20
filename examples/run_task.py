from asyncio import run as aiorun

import typer
from rich import print as rprint

import workflowai
from examples.city_to_capital_task import CityToCapitalTask, CityToCapitalTaskInput


def main(city: str) -> None:
    client = workflowai.start()
    task = CityToCapitalTask()

    async def _inner() -> None:
        task_input = CityToCapitalTaskInput(city=city)
        task_run = await client.run(task, task_input)

        rprint(task_run.task_output)

    aiorun(_inner())


if __name__ == "__main__":
    typer.run(main)
