from pydantic import BaseModel

from workflowai import Run, agent
from workflowai.core.domain.model import Model
from workflowai.core.domain.tool import Tool
from workflowai.core.domain.tool_call import ToolCallResult
from workflowai.core.domain.version_properties import VersionProperties


class AnswerQuestionInput(BaseModel):
    question: str


class AnswerQuestionOutput(BaseModel):
    answer: str = ""


_GET_CURRENT_TIME_TOOL = Tool(
    name="get_current_time",
    description="Get the current time",
    input_schema={},
    output_schema={
        "properties": {
            "time": {"type": "string", "description": "The current time"},
        },
    },
)


@agent(
    id="answer-question",
    version=VersionProperties(model=Model.GPT_4O_LATEST, enabled_tools=[_GET_CURRENT_TIME_TOOL]),
)
async def answer_question(_: AnswerQuestionInput) -> Run[AnswerQuestionOutput]: ...


async def test_tools():
    run = await answer_question(AnswerQuestionInput(question="What is the current time spelled out in French?"))
    assert not run.output.answer

    assert run.tool_call_requests
    assert len(run.tool_call_requests) == 1
    assert run.tool_call_requests[0].name == "get_current_time"

    replied = await run.reply(tool_results=[ToolCallResult(id=run.tool_call_requests[0].id, output={"time": "12:00"})])
    assert replied.output.answer
