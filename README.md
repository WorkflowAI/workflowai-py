# WorkflowAI Python

A library to use WorkflowAI with Python

## Context

WorkflowAI is a platform for building agents.

## Installation

`workflowai` requires a python >= 3.9.

```sh
pip install workflowai
```

## Usage

Usage examples are available in the [examples](./examples/) directory or end to [end test](./tests/e2e/)
directory.

### Getting a workflowai api key

Create an account on [workflowai.com](https://workflowai.com), generate an API key and set it as
an environment variable.

```
WORKFLOWAI_API_KEY=...
```

> You can also set the `WORKFLOWAI_API_URL` environment variable to point to your own WorkflowAI instance.

> The current UI does not allow to generate an API key without creating a task. Take the opportunity to play
> around with the UI. When the task is created, you can generate an API key from the Code section

### Set up the workflowai client

If you have defined the api key using an environment variable, the shared workflowai client will be
correctly configured.

You can override the shared client by calling the init function.

```python
import workflowai

workflowai.init(
    url=..., # defaults to WORKFLOWAI_API_URL env var or https://api.workflowai.com
    api_key=..., # defaults to WORKFLOWAI_API_KEY env var
)
```

#### Using multiple clients

You might want to avoid using the shared client, for example if you are using multiple API keys or accounts.
It is possible to achieve this by manually creating client instances

```python
from workflowai import WorkflowAI

client = WorkflowAI(
    url=...,
    api_key=...,
)

# Use the client to create and run agents
@client.agent()
def my_agent(task_input: Input) -> Output:
    ...
```

### Build agents

An agent is in essence an async function with the added constraints that:

- it has a single argument that is a pydantic model
- it has a single return value that is a pydantic model
- it is decorated with the `@client.agent()` decorator

> [Pydantic](https://docs.pydantic.dev/latest/) is a very popular and powerful library for data validation and
> parsing. It allows us to extract the input and output schema in a simple way

Below is an agent that says hello:

```python
import workflowai
from pydantic import BaseModel

class Input(BaseModel):
    name: str

class Output(BaseModel):
    greeting: str

@workflowai.agent()
async def say_hello(input: Input) -> Output:
    """Say hello"""
    ...
```

When you call that function, the associated agent will be created on workflowai.com if it does not exist yet and a
run will be created. By default:

- the docstring will be used as instructions for the agent
- the default model (`workflowai.DEFAULT_MODEL`) is used to run the agent
- the agent id will be a slugified version of the function name (i-e `say-hello`) in this case

> **What is "..." ?**
>
> The `...` is the ellipsis value in python. It is usually used as a placeholder. You could use "pass" here as well
> or anything really, the implementation of the function is handled by the decorator `@workflowai.agent()` and so
> the function body is not executed.
> `...` is usually the right choice because it signals type checkers that they should ignore the function body.

> Having the agent id determined at runtime can lead to unexpected changes, since changing the function name will
> change the agent id. A good practice is to set the agent id explicitly, `@workflowai.agent(id="say-hello")`.

#### Using different models

WorkflowAI supports a long list of models. The source of truth for models we support is on [workflowai.com](https://workflowai.com). The [Model enum](./workflowai/core/domain/model.py) is a good indication of what models are supported at the time of the sdk release, although it may be missing some models since new ones are added all the time.

You can set the model explicitly in the agent decorator:

```python
@workflowai.agent(model=Model.GPT_4O_LATEST)
def say_hello(input: Input) -> Output:
    ...
```

> Models do not become invalid on WorkflowAI. When a model is retired, it will be replaced dynamically by
> a newer version of the same model with the same or a lower price so calling the api with
> a retired model will always work.

### Version from code or deployments

Setting a docstring or a model in the agent decorator signals the client that the agent parameters are
fixed and configured via code.

Handling the agent parameters in code is useful to get started but may be limited in the long run:

- it is somewhat hard to measure the impact of different parameters
- moving to new models or instructions requires a deployment
- iterating on the agent parameters can be very tedious

Deployments allow you to refer to a version of an agent's parameters from your code that's managed from the
workflowai.com UI. The following code will use the version of the agent named "production" which is a lot
more flexible than changing the function parameters when running in production.

```python
@workflowai.agent(deployment="production") # or simply @workflowai.agent()
def say_hello(input: Input) -> AsyncIterator[Run[Output]]:
    ...
```

### Streaming and advanced usage

You can configure the agent function to stream or return the full run object, simply by changing the type annotation.

```python
# Return the full run object, useful if you want to extract metadata like cost or duration
@workflowai.agent()
async def say_hello(input: Input) -> Run[Output]:
    ...

# Stream the output, the output is filled as it is generated
@workflowai.agent()
def say_hello(input: Input) -> AsyncIterator[Output]:
    ...

# Stream the run object, the output is filled as it is generated
@workflowai.agent()
def say_hello(input: Input) -> AsyncIterator[Run[Output]]:
    ...
```

### Tools

Tools allow enhancing an agent's capabilities by allowing it to call external functions.

#### WorkflowAI Hosted tools

WorkflowAI hosts a few tools:

- `@browser-text` allows fetching the content of a web page
- `@search` allows performing a web search

Hosted tools tend to be faster because there is no back and forth between the client and the WorkflowAI API. Instead,
if a tool call is needed, the WorkflowAI API will call it within a single request.

A single run will be created for all tool iterations.

To use a tool, simply add it's handles to the instructions (the function docstring):

```python
@workflowai.agent()
def say_hello(input: Input) -> Output:
    """
    You can use @search and @browser-text to retrieve information about the name.
    """
    ...
```

#### Custom tools

Custom tools allow using most functions within a single agent call. If an agent has custom tools, and the model
deems that tools are needed for a particular run, the agent will:

- call all tools in parallel
- wait for all tools to complete
- reply to the run with the tool outputs
- continue with the next step of the run, and re-execute tools if needed
- ...
- until either no tool calls are requested, the max iteration (10 by default) or the agent has run to completion

Tools are defined as regular python functions, and can be async or sync. Examples for tools are available in the [tools end 2 end test file](./tests/e2e/tools_test.py).

> **Important**: It must be possible to determine the schema of a tool from the function signature. This means that
> the function must have type annotations and use standard types or `BaseModel` only for now.

```python
# Annotations for parameters are passed as property descriptions in the tool schema
def get_current_time(timezone: Annotated[str, "The timezone to get the current time in. e-g Europe/Paris"]) -> str:
    """Return the current time in the given timezone in iso format"""
    return datetime.now(ZoneInfo(timezone)).isoformat()

@agent(
    id="answer-question",
    tools=[get_current_time],
    version=VersionProperties(model=Model.GPT_4O_LATEST),
)
async def answer_question(_: AnswerQuestionInput) -> Run[AnswerQuestionOutput]: ...

run = await answer_question(AnswerQuestionInput(question="What is the current time in Paris?"))
assert run.output.answer
```

> It's important to understand that there are actually two runs in a single agent call:
>
> - the first run returns an empty output with a tool call request with a timezone
> - the second run returns the current time in the given timezone
>
> Only the last run is returned to the caller.

### Error handling

Agents can raise errors, for example when the underlying model fails to generate a response or when
there are content moderation issues.

All errors are wrapped in a `WorkflowAIError` that contains details about what happened.
The most interesting fields are:

- `code` is a string that identifies the type of error, see the [errors.py](./workflowai/core/domain/errors.py) file for more details
- `message` is a human readable message that describes the error

The `WorkflowAIError` is raised when the agent is called, so you can handle it like any other exception.

```python
try:
    await say_hello(Input(name="John"))
except WorkflowAIError as e:
    print(e.code)
    print(e.message)
```

### Definining input and output types

There are some important subtleties when defining input and output types.

#### Descriptions and examples

Field description and examples are passed to the model and can help stir the output in the right direction. A good
use case is to describe a format or style for a string field

```python
# summary has no examples or description so the model will likely return a block of text
class SummaryOutput(BaseModel):
    summary: str

# passing the description will help the model return a summary formatted as bullet points
class SummaryOutput(BaseModel):
    summary: str = Field(description="A summary, formatted as bullet points")

# passing examples can help as well
class SummaryOutput(BaseModel):
    summary: str = Field(examples=["- Paris is a city in France\n- London is a city in England"])
```

Some notes:

- there are very little use cases for descriptions and examples in the **input** type. The model will most of the
  infer from the value that is passed. An example use case is to use the description for fields that can be missing.
- adding examples that are too numerous or too specific can push the model to restrict the output value

#### Required versus optional fields

In short, we recommend using default values for most output fields.

Pydantic is by default rather strict on model validation. If there is no default value, the field must be provided.
Although the fact that a field is required is passed to the model, the generation can sometimes omit null or empty
values.

```python
class Input(BaseModel):
    name: str

class OutputStrict(BaseModel):
    greeting: str

@workflowai.agent()
async def say_hello_strict(_: Input) -> OutputStrict:
    ...

try:
    run = await say_hello(Input(name="John"))
    print(run.output.greeting) # "Hello, John!"
except WorkflowAIError as e:
    print(e.code) # "invalid_generation" error code means that the generation did not match the schema

class OutputTolerant(BaseModel):
    greeting: str = ""

@workflowai.agent()
async def say_hello_tolerant(_: Input) -> OutputTolerant:
    ...

# The invalid_generation is less likely
run = await say_hello_tolerant(Input(name="John"))
if not run.output.greeting:
    print("No greeting was generated !")
print(run.output.greeting) # "Hello, John!"

```

> WorkflowAI automatically retries invalid generations once. If a model outputs an object that does not match the
> schema, a new generation is triggered with the previous response and the error message as context.

Another reason to prefer optional fields in the output is for streaming. Partial outputs are constructed using
`BaseModel.model_construct` when streaming. If a default value is not provided for a field, fields that are
absent will cause `AttributeError` when queried.

```python
class Input(BaseModel):
    name: str

class OutputStrict(BaseModel):
    greeting1: str
    greeting2: str

@workflowai.agent()
def say_hello_strict(_: Input) -> AsyncIterator[Output]:
    ...

async for run in say_hello(Input(name="John")):
    try:
        print(run.output.greeting1)
    except AttributeError:
        # run.output.greeting1 has not been generated yet


class OutputTolerant(BaseModel):
    greeting1: str = ""
    greeting2: str = ""

@workflowai.agent()
def say_hello_tolerant(_: Input) -> AsyncIterator[OutputTolerant]:
    ...

async for run in say_hello(Input(name="John")):
    print(run.output.greeting1) # will be empty if the model has not generated it yet

```
