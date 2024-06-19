from pydantic import BaseModel

from workflowai.core.domain.task import Task


class HelloTaskInput(BaseModel):
    name: str


class HelloTaskOutput(BaseModel):
    message: str


class HelloTask(Task[HelloTaskInput, HelloTaskOutput]):
    input_class: type[HelloTaskInput] = HelloTaskInput
    output_class: type[HelloTaskOutput] = HelloTaskOutput
