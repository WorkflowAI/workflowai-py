from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

from workflowai import Task, VersionReference


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


class CityToCapitalTask(Task[CityToCapitalTaskInput, CityToCapitalTaskOutput]):
    id: str = "citytocapital"
    schema_id: int = 1
    input_class: type[CityToCapitalTaskInput] = CityToCapitalTaskInput
    output_class: type[CityToCapitalTaskOutput] = CityToCapitalTaskOutput

    version: VersionReference = 4
