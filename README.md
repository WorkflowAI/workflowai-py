# WorkflowAI Python

A library to use [WorkflowAI](https://workflowai.com) with Python.

## Context

[WorkflowAI](https://workflowai.com) is a platform for designing, building, and deploying agents.

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

Below is an agent that analyzes customer feedback from call transcripts:

```python
import workflowai
from pydantic import BaseModel, Field
from typing import List
from datetime import date

# Input model for the call feedback analysis
class CallFeedbackInput(BaseModel):
    """Input for analyzing a customer feedback call."""
    transcript: str = Field(description="The full transcript of the customer feedback call.")
    call_date: date = Field(description="The date when the call took place.")

# Model representing a single feedback point with supporting evidence
class FeedbackPoint(BaseModel):
    """A specific feedback point with its supporting quote."""
    point: str = Field(description="The main point or insight from the feedback.")
    quote: str = Field(description="The exact quote from the transcript supporting this point.")
    timestamp: str = Field(description="The timestamp or context of when this was mentioned in the call.")

# Model representing the structured analysis of the customer feedback call
class CallFeedbackOutput(BaseModel):
    """Structured analysis of the customer feedback call."""
    positive_points: List[FeedbackPoint] = Field(
        default_factory=list,
        description="List of positive feedback points, each with a supporting quote."
    )
    negative_points: List[FeedbackPoint] = Field(
        default_factory=list,
        description="List of negative feedback points, each with a supporting quote."
    )

@workflowai.agent(id="analyze-call-feedback", model=Model.GPT_4O_LATEST)
async def analyze_call_feedback(input: CallFeedbackInput) -> CallFeedbackOutput:
    """
    Analyze a customer feedback call transcript to extract key insights:
    1. Identify positive feedback points with supporting quotes
    2. Identify negative feedback points with supporting quotes
    3. Include timestamp/context for each point
    
    Be specific and objective in the analysis. Use exact quotes from the transcript.
    Maintain the customer's original wording in quotes.
    """
    ...
```

When you call that function, the associated agent will be created on workflowai.com if it does not exist yet and a
run will be created. By default:

- the docstring will be used as instructions for the agent
- the default model (`workflowai.DEFAULT_MODEL`) is used to run the agent
- the agent id will be a slugified version of the function name unless specified explicitly

Example usage:

```python
# Example transcript
transcript = '''
[00:01:15] Customer: I've been using your software for about 3 months now, and I have to say the new dashboard feature is really impressive. It's saving me at least an hour each day on reporting.

[00:02:30] Customer: However, I'm really frustrated with the export functionality. It crashed twice this week when I tried to export large reports, and I lost all my work.

[00:03:45] Customer: On a positive note, your support team, especially Sarah, was very responsive when I reported the issue. She got back to me within minutes.

[00:04:30] Customer: But I think the pricing for additional users is a bit steep compared to other solutions we looked at.
'''

# Analyze the feedback
result = await analyze_call_feedback(
    CallFeedbackInput(
        transcript=transcript,
        call_date=date(2024, 1, 15)
    )
)

# Print the analysis
print("\nPositive Points:")
for point in result.positive_points:
    print(f"\n• {point.point}")
    print(f"  Quote [{point.timestamp}]: \"{point.quote}\"")

print("\nNegative Points:")
for point in result.negative_points:
    print(f"\n• {point.point}")
    print(f"  Quote [{point.timestamp}]: \"{point.quote}\"")
```

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
async def analyze_call_feedback(input: CallFeedbackInput) -> CallFeedbackOutput:
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
async def analyze_call_feedback(input: CallFeedbackInput) -> AsyncIterator[Run[CallFeedbackOutput]]:
    ...
```

### Streaming and advanced usage

You can configure the agent function to stream or return the full run object, simply by changing the type annotation.

```python
# Return the full run object, useful if you want to extract metadata like cost or duration
@workflowai.agent()
async def analyze_call_feedback(input: CallFeedbackInput) -> Run[CallFeedbackOutput]:
    ...

# Stream the output, the output is filled as it is generated
@workflowai.agent()
async def analyze_call_feedback(input: CallFeedbackInput) -> AsyncIterator[CallFeedbackOutput]:
    ...

# Stream the run object, the output is filled as it is generated
@workflowai.agent()
async def analyze_call_feedback(input: CallFeedbackInput) -> AsyncIterator[Run[CallFeedbackOutput]]:
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
async def analyze_call_feedback(input: CallFeedbackInput) -> CallFeedbackOutput:
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
    await analyze_call_feedback(
        CallFeedbackInput(
            transcript="[00:01:15] Customer: The product is great!",
            call_date=date(2024, 1, 15)
        )
    )
except WorkflowAIError as e:
    print(e.code)
    print(e.message)
```

### Defining input and output types

There are some important subtleties when defining input and output types.

#### Descriptions and examples

Field description and examples are passed to the model and can help stir the output in the right direction. A good
use case is to describe a format or style for a string field

```python
# point has no examples or description so the model will be less guided
class BasicFeedbackPoint(BaseModel):
    point: str

# passing the description helps guide the model's output format
class DetailedFeedbackPoint(BaseModel):
    point: str = Field(
        description="A clear, specific point of feedback extracted from the transcript."
    )

# passing examples can help as well
class FeedbackPoint(BaseModel):
    point: str = Field(
        description="A clear, specific point of feedback extracted from the transcript.",
        examples=[
            "Dashboard feature saves significant time on reporting",
            "Export functionality is unstable with large reports"
        ]
    )
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
class CallFeedbackOutputStrict(BaseModel):
    positive_points: List[FeedbackPoint]
    negative_points: List[FeedbackPoint]

@workflowai.agent()
async def analyze_call_feedback_strict(input: CallFeedbackInput) -> CallFeedbackOutputStrict:
    ...

try:
    result = await analyze_call_feedback_strict(
        CallFeedbackInput(
            transcript="[00:01:15] Customer: The product is great!",
            call_date=date(2024, 1, 15)
        )
    )
except WorkflowAIError as e:
    print(e.code) # "invalid_generation" error code means that the generation did not match the schema

class CallFeedbackOutputTolerant(BaseModel):
    positive_points: List[FeedbackPoint] = Field(default_factory=list)
    negative_points: List[FeedbackPoint] = Field(default_factory=list)

@workflowai.agent()
async def analyze_call_feedback_tolerant(input: CallFeedbackInput) -> CallFeedbackOutputTolerant:
    ...

# The invalid_generation is less likely
result = await analyze_call_feedback_tolerant(
    CallFeedbackInput(
        transcript="[00:01:15] Customer: The product is great!",
        call_date=date(2024, 1, 15)
    )
)
if not result.positive_points and not result.negative_points:
    print("No feedback points were generated!")
```

> WorkflowAI automatically retries invalid generations once. If a model outputs an object that does not match the
> schema, a new generation is triggered with the previous response and the error message as context.

Another reason to prefer optional fields in the output is for streaming. Partial outputs are constructed using
`BaseModel.model_construct` when streaming. If a default value is not provided for a field, fields that are
absent will cause `AttributeError` when queried.

```python
@workflowai.agent()
async def analyze_call_feedback_stream(input: CallFeedbackInput) -> AsyncIterator[CallFeedbackOutput]:
    ...

async for result in analyze_call_feedback_stream(
    CallFeedbackInput(
        transcript="[00:01:15] Customer: The product is great!",
        call_date=date(2024, 1, 15)
    )
):
    # With default values, we can safely check the points as they stream in
    print(f"Positive points so far: {len(result.positive_points)}")
    print(f"Negative points so far: {len(result.negative_points)}")
```
