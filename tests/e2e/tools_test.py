from datetime import datetime
from typing import Annotated

from pydantic import BaseModel
from zoneinfo import ZoneInfo

from workflowai import Run, agent
from workflowai.core.domain.model import Model
from workflowai.core.domain.tool import ToolDefinition
from workflowai.core.domain.tool_call import ToolCallResult
from workflowai.core.domain.version_properties import VersionProperties


class AnswerQuestionInput(BaseModel):
    question: str


class AnswerQuestionOutput(BaseModel):
    answer: str = ""


async def test_manual_tool():
    get_current_time_tool = ToolDefinition(
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
        version=VersionProperties(model=Model.GPT_4O_LATEST, enabled_tools=[get_current_time_tool]),
    )
    async def answer_question(_: AnswerQuestionInput) -> Run[AnswerQuestionOutput]: ...

    run = await answer_question(AnswerQuestionInput(question="What is the current time spelled out in French?"))
    assert not run.output.answer

    assert run.tool_call_requests
    assert len(run.tool_call_requests) == 1
    assert run.tool_call_requests[0].name == "get_current_time"

    replied = await run.reply(tool_results=[ToolCallResult(id=run.tool_call_requests[0].id, output={"time": "12:00"})])
    assert replied.output.answer


async def test_auto_tool():
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
