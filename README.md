# WorkflowAI Python

[![PyPI version](https://img.shields.io/pypi/v/workflowai.svg)](https://pypi.org/project/workflowai/)

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
    url=..., # defaults to WORKFLOWAI_API_URL env var or https://run.workflowai.com (our [globally distributed, highly available endpoint](https://docs.workflowai.com/workflowai-cloud/reliability))
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
def my_agent(agent_input: Input) -> Output:
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
    positive_points: list[FeedbackPoint] = Field(
        default_factory=list,
        description="List of positive feedback points, each with a supporting quote."
    )
    negative_points: list[FeedbackPoint] = Field(
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

# Create input
feedback_input = CallFeedbackInput(
    transcript=transcript,
    call_date=date(2024, 1, 15)
)

# Analyze the feedback
run = await analyze_call_feedback(feedback_input)

# Print the analysis
print("\nPositive Points:")
for point in run.positive_points:
    print(f"\n• {point.point}")
    print(f"  Quote [{point.timestamp}]: \"{point.quote}\"")

print("\nNegative Points:")
for point in run.negative_points:
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

You can specify the model in two ways:

1. In the agent decorator:

```python
from workflowai import Model

@workflowai.agent(model=Model.GPT_4O_LATEST)
async def analyze_call_feedback(input: CallFeedbackInput) -> CallFeedbackOutput:
    ...
```

2. As a function parameter when calling the agent:

```python
@workflowai.agent(id="analyze-call-feedback")
async def analyze_call_feedback(input: CallFeedbackInput) -> CallFeedbackOutput:
    ...

# Call with specific model
result = await analyze_call_feedback(input_data, model=Model.GPT_4O_LATEST)
```

This flexibility allows you to either fix the model in the agent definition or dynamically choose different models at runtime.

> Models do not become invalid on WorkflowAI. When a model is retired, it will be replaced dynamically by
> a newer version of the same model with the same or a lower price so calling the api with
> a retired model will always work.

### Using templated instructions

You can use [Jinja2](https://jinja.palletsprojects.com/)-style templating in your agent's instructions (docstring) to make them dynamic based on input values. The template variables are automatically populated from the fields in your input model.

```python
class CodeReviewInput(BaseModel):
    language: str = Field(description="Programming language of the code")
    style_guide: str = Field(description="Style guide to follow")
    is_production: bool = Field(description="Whether this is a production review")
    focus_areas: list[str] = Field(description="Areas to focus on during review", default_factory=list)

class CodeReviewOutput(BaseModel):
    """Output from a code review."""
    issues: list[str] = Field(
        default_factory=list,
        description="List of identified issues or suggestions for improvement"
    )
    compliments: list[str] = Field(
        default_factory=list,
        description="List of positive aspects and good practices found in the code"
    )
    summary: str = Field(
        description="A brief summary of the code review findings"
    )

@workflowai.agent(id="code-review")
async def review_code(review_input: CodeReviewInput) -> CodeReviewOutput:
    """
    You are a code reviewer for {{ language }} code.
    Please review according to the {{ style_guide }} style guide.

    {% if is_production %}
    This is a PRODUCTION review - be extra thorough and strict.
    {% else %}
    This is a development review - focus on maintainability.
    {% endif %}

    {% if focus_areas %}
    Key areas to focus on:
    {% for area in focus_areas %}
    {{ loop.index }}. {{ area }}
    {% endfor %}
    {% endif %}
    """
    ...
```

The template uses [Jinja2](https://jinja.palletsprojects.com/) syntax and supports common templating features including:

- Variable substitution: `{{ variable }}`
- Conditionals: `{% if condition %}...{% endif %}`
- Loops: `{% for item in items %}...{% endfor %}`
- Loop indices: `{{ loop.index }}`

See the [Jinja2 documentation](https://jinja.palletsprojects.com/) for the full template syntax and capabilities.

We recommend using ChatGPT or CursorAI to help generate the template.

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
def analyze_call_feedback(input: CallFeedbackInput) -> AsyncIterator[Run[CallFeedbackOutput]]:
    ...
```

#### The Agent class

Any agent function (aka a function decorated with `@workflowai.agent()`) is in fact an instance
of the `Agent` class. Which means that any defined agent can access the underlying agent functions, mainly
`run`, `stream` and `reply`. The `__call__` method of the agent is overriden for convenience to match the original
function signature.

```python
# Any agent definition would also work
@workflowai.agent()
def analyze_call_feedback(input: CallFeedbackInput) -> CallFeedbackOutput:
    ...

# It is possible to call the run function directly to get a run object if needed
run = await agent.run(CallFeedbackInput(...))
# Or the stream function to get a stream of run objects (see below)
chunks = [chunk async for chunk in agent.stream(CallFeedbackInput(...))
# Or reply to manually to a given run id (see reply below)
run = await agent.reply(run_id="...", user_message="...", tool_results=...)
```

### The Run object

Although having an agent only return the run output covers most use cases, some use cases require having more
information about the run.

By changing the type annotation of the agent function to `Run[Output]`, the generated function will return
the full run object.

```python
@workflowai.agent()
async def analyze_call_feedback(input: CallFeedbackInput) -> Run[CallFeedbackOutput]:
    ...


run = await analyze_call_feedback(feedback_input)
print(run.output) # the output, as before
print(run.model) # the model used for the run
print(run.cost_usd) # the cost of the run in USD
print(run.duration_seconds) # the duration of the inference in seconds
```

### Streaming

You can configure the agent function to stream by changing the type annotation to an AsyncIterator.

#### Streaming the output only

Use `AsyncIterator[Output]` to get the **output** as it is generated.

```python
from collections.abc import AsyncIterator

# Stream the output, the output is filled as it is generated
@workflowai.agent()
def analyze_call_feedback(input: CallFeedbackInput) -> AsyncIterator[CallFeedbackOutput]:
    ...

async for chunk in analyze_call_feedback(feedback_input):
    # Just get the output as it's generated
    print(chunk.output)
```

> Note: no need to mark the agent as async here ! It is already asynchronous since it returns an AsyncIterator.
> The type checkers some times get confused since they consider that an async function that returns an AsyncIterator is
> async twice.
> For example, a function with the signature `async def foo() -> AsyncIterator[int]` may be called
> `async for c in await foo():...` in certain cases...

#### Streaming the run object

Use `AsyncIterator[Run[Output]]` to get the **run** object as it is generated, which allows you, for the **last chunk**, to access the cost and duration of the run.

```python
import workflowai
from workflowai import Run
from collections.abc import AsyncIterator

# Stream the run object, the output is filled as it is generated
@workflowai.agent()
def analyze_call_feedback(input: CallFeedbackInput) -> AsyncIterator[Run[CallFeedbackOutput]]:
    ...

last_chunk = None

async for chunk in analyze_call_feedback(feedback_input):
    # Show output as it's generated
    print(chunk.output)
    last_chunk = chunk

if last_chunk:
    # Cost and duration are only available on the last chunk
    print(f"\nCost: ${last_chunk.cost_usd}")
    print(f"Latency: {last_chunk.duration_seconds:.2f}s")
```

### Images

Add images as input to an agent by using the `Image` class. An image can either have:

- a `content`, base64 encoded data
- a `url`

```python
from workflowai.fields import Image

class ImageInput(BaseModel):
    image: Image = Field(description="The image to analyze")

# use base64 to include the image inline
image = Image(content_type='image/jpeg', data='<base 64 encoded data>')

# You can also use the `url` property to pass an image URL.
image = Image(url="https://example.com/image.jpg")
```

An example of using image as input is available in [07_image_agent.py](./examples/07_image_agent.py).

### Files (PDF, .txt, ...)

Use the `File` class to pass files as input to an agent. Different LLMs support different file types.

```python
from workflowai.fields import File
...

class PDFQuestionInput(BaseModel):
    pdf: File = Field(description="The PDF document to analyze")
    question: str = Field(description="The question to answer about the PDF content")

class PDFAnswerOutput(BaseModel):
    answer: str = Field(description="The answer to the question based on the PDF content")
    quotes: list[str] = Field(description="Relevant quotes from the PDF that support the answer")

@workflowai.agent(id="pdf-answer", model=Model.CLAUDE_3_5_SONNET_LATEST)
async def answer_pdf_question(input: PDFQuestionInput) -> PDFAnswerOutput:
    """
    Analyze the provided PDF document and answer the given question.
    Provide a clear and concise answer based on the content found in the PDF.
    """
    ...

pdf = File(content_type='application/pdf', data='<base 64 encoded data>')
question = "What are the key findings in this report?"

output = await answer_pdf_question(PDFQuestionInput(pdf=pdf, question=question))
# Print the answer and supporting quotes
print("Answer:", output.answer)
print("Supporting quotes:", "\n -".join(("", *quotes))
for quote in output.quotes:
    print(f"- {quote}")
```

An example of using a PDF as input is available in [pdf_answer.py](./examples/pdf_answer.py).

### Audio

Use the `File` class to pass audio files as input to an agent. Note that only some models support audio input.

```python
from workflowai.fields import File
...

class AudioInput(BaseModel):
    audio: File = Field(description="The audio recording to analyze for spam/robocall detection")

class AudioClassification(BaseModel):
    is_spam: bool = Field(description="Whether the audio is classified as spam/robocall")

@workflowai.agent(id="audio-classifier", model=Model.GEMINI_1_5_FLASH_LATEST)
async def classify_audio(input: AudioInput) -> AudioClassification:
    ...

# Example 1: Using base64 encoded data
audio = File(content_type='audio/mp3', data='<base 64 encoded data>')

# Example 2: Using a URL
# audio = File(url='https://example.com/audio/call.mp3')

run = await classify_audio(AudioInput(audio=audio))
print(run)
```

See an example of audio classification in [audio_classifier.py](./examples/04_audio_classifier.py).

### Caching

By default, the cache settings is `auto`, meaning that agent runs are cached when the temperature is 0
(the default temperature value). Which means that, when running the same agent twice with the **exact** same input,
the exact same output is returned and the underlying model is not called a second time.

The cache usage string literal is defined in [cache_usage.py](./workflowai/core/domain/cache_usage.py) file. There are 3 possible values:

- `auto`: (default) Use cached results only when temperature is 0
- `always`: Always use cached results if available, regardless of model temperature
- `never`: Never use cached results, always execute a new run

The cache usage can be passed to the agent function as a keyword argument:

```python
@workflowai.agent(id="analyze-call-feedback")
async def analyze_call_feedback(_: CallFeedbackInput) -> AsyncIterator[CallFeedbackOutput]: ...

run = await analyze_call_feedback(CallFeedbackInput(...), use_cache="always")
```

<!-- TODO: add cache usage at agent level when available -->

### Replying to a run

Some use cases require the ability to have a back and forth between the client and the LLM. For example:

- tools [see below](#tools) use the reply ability internally
- chatbots
- correcting the LLM output

In WorkflowAI, this is done by replying to a run. A reply can contain:

- a user response
- tool results

<!-- TODO: find a better example for reply -->

```python
# Important: returning the full run object is required to use the reply feature
@workflowai.agent()
async def say_hello(input: Input) -> Run[Output]:
    ...

run = await say_hello(Input(name="John"))
run = await run.reply(user_message="Now say hello to his brother James")
```

The output of a reply to a run has the same type as the original run, which makes it easy to iterate towards the
construction of a final output.

> To allow run iterations, it is very important to have outputs that are tolerant to missing fields, aka that
> have default values for most of their fields. Otherwise the agent will throw a WorkflowAIError on missing fields
> and the run chain will be broken.

> Under the hood, `run.reply` calls the `say_hello.reply` method as described in the
> [Agent class](#the-agent-class) section.

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

# Tools can also be async
async def fetch_webpage(url: str) -> str:
    """Fetch the content of a webpage"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

@agent(
    id="answer-question",
    tools=[get_current_time, fetch_webpage],
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

#### Recoverable errors

Sometimes, the LLM outputs an object that is partially valid, good examples are:

- the model context window was exceeded during the generation
- the model decided that a tool call result was a failure

In this case, an agent that returns an output only will always raise an `InvalidGenerationError` which
subclasses `WorkflowAIError`.

However, an agent that returns a full run object will try to recover from the error by using the partial output.

```python

run = await agent(input=Input(name="John"))

# The run will have an error
assert run.error is not None

# The run will have a partial output
assert run.output is not None
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
    positive_points: list[FeedbackPoint]
    negative_points: list[FeedbackPoint]

@workflowai.agent()
async def analyze_call_feedback_strict(input: CallFeedbackInput) -> CallFeedbackOutputStrict:
    ...

try:
    run = await analyze_call_feedback_strict(
        CallFeedbackInput(
            transcript="[00:01:15] Customer: The product is great!",
            call_date=date(2024, 1, 15)
        )
    )
except WorkflowAIError as e:
    print(e.code) # "invalid_generation" error code means that the generation did not match the schema

class CallFeedbackOutputTolerant(BaseModel):
    positive_points: list[FeedbackPoint] = Field(default_factory=list)
    negative_points: list[FeedbackPoint] = Field(default_factory=list)

@workflowai.agent()
async def analyze_call_feedback_tolerant(input: CallFeedbackInput) -> CallFeedbackOutputTolerant:
    ...

# The invalid_generation is less likely
run = await analyze_call_feedback_tolerant(
    CallFeedbackInput(
        transcript="[00:01:15] Customer: The product is great!",
        call_date=date(2024, 1, 15)
    )
)
if not run.positive_points and not run.negative_points:
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

async for run in analyze_call_feedback_stream(
    CallFeedbackInput(
        transcript="[00:01:15] Customer: The product is great!",
        call_date=date(2024, 1, 15)
    )
):
    print(f"Positive points so far: {len(run.positive_points)}")
    print(f"Negative points so far: {len(run.negative_points)}")
```

#### Field properties

Pydantic allows a variety of other validation criteria for fields: minimum, maximum, pattern, etc.
This additional criteria are included the JSON Schema that is sent to WorkflowAI, and are sent to the model.

```python
class Input(BaseModel):
    name: str = Field(min_length=3, max_length=10)
    age: int = Field(ge=18, le=100)
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
```

These arguments can be used to stir the model in the right direction. The caveat is have a
validation that is too strict can lead to invalid generations. In case of an invalid generation:

- WorkflowAI retries the inference once by providing the model with the invalid output and the validation error
- if the model still fails to generate a valid output, the run will fail with an `InvalidGenerationError`.
  the partial output is available in the `partial_output` attribute of the `InvalidGenerationError`

```python

@agent()
def my_agent(_: Input) -> :...
```

## Workflows

For advanced workflow patterns and examples, please refer to the [Workflows README](examples/workflows/README.md) for more details.

## Contributing

See the [CONTRIBUTING.md](./CONTRIBUTING.md) file for more details.
