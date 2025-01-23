from pydantic import BaseModel


class HelloTaskInput(BaseModel):
    name: str


class HelloTaskOutput(BaseModel):
    message: str


class HelloTaskOutputNotOptional(HelloTaskOutput):
    message: str
    another_field: str
