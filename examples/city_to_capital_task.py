from asyncio import run as aiorun

import typer
from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]
from rich import print as rprint

import workflowai


class CityToCapitalTaskInput(BaseModel):
    city: str = Field(
        description="The name of the city for which the capital is to be found",
        examples=["Tokyo"],
    )


class CityToCapitalTaskOutput(BaseModel):
    capital: str = Field(
        description="The capital of the specified city",
        examples=["Tokyo"],
    )


@workflowai.task(schema_id=1)
async def city_to_capital(task_input: CityToCapitalTaskInput) -> CityToCapitalTaskOutput: ...


def main(city: str) -> None:
    async def _inner() -> None:
        task_input = CityToCapitalTaskInput(city=city)
        output = await city_to_capital(task_input)

        rprint(output)

    aiorun(_inner())


if __name__ == "__main__":
    typer.run(main)
