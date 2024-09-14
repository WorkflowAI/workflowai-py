# WorkflowAI Python

A library to use WorkflowAI with Python

## Installation

`workflowai` requires a python >= 3.9.

```sh
pip install workflowai
```

## Usage

Usage examples are available in the [examples](./examples/) directory.

### Set up the workflowai client

```python
import workflowai

wai = workflowai.start(
    url=..., # defaults to WORKFLOWAI_API_URL env var or https://api.workflowai.com
    api_key=..., # defaults to WORKFLOWAI_API_KEY env var
)
```

### Define a task

We use pydantic for type definitions.

```python
from pydantic import BaseModel, Field

from workflowai import Task, TaskVersionReference

class CityToCapitalTaskInput(BaseModel):
    city: str


class CityToCapitalTaskOutput(BaseModel):
    capital: str

class CityToCapitalTask(Task[CityToCapitalTaskInput, CityToCapitalTaskOutput]):
    id: str = "citytocapital"
    schema_id: int = 1
    input_class: type[CityToCapitalTaskInput] = CityToCapitalTaskInput
    output_class: type[CityToCapitalTaskOutput] = CityToCapitalTaskOutput

    # The default version that should be used when running the task
    version: TaskVersionReference = TaskVersionReference(
        iteration=4,
    )
```

### Run a task

```python
task = CityToCapitalTask()
task_input = CityToCapitalTaskInput(city=city)
task_run = await wai.run(task, task_input)

print(task_run.task_output)
```

It is also possible to stream a task output

```python
task = CityToCapitalTask()
task_input = CityToCapitalTaskInput(city=city)
iterator = await wai.run(task, task_input, stream=True)
async for chunk in iterator:
    print(chunk) # chunk is a partial (non validated) CityToCapitalTaskOutput
```
