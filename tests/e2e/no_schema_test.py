from typing import Optional

from pydantic import BaseModel

import workflowai


class SummarizeTaskInput(BaseModel):
    text: Optional[str] = None


class SummarizeTaskOutput(BaseModel):
    summary_points: Optional[list[str]] = None


@workflowai.agent(id="summarize", model="gemini-1.5-flash-latest")
async def summarize(task_input: SummarizeTaskInput) -> SummarizeTaskOutput: ...


async def test_summarize():
    summarized = await summarize(SummarizeTaskInput(text="Hello, world!"))
    assert summarized.summary_points
