from typing import Optional

from pydantic import BaseModel

import workflowai


class SummarizeTaskInput(BaseModel):
    text: Optional[str] = None


class SummarizeTaskOutput(BaseModel):
    summary: Optional[str] = None


@workflowai.agent(id="summarize")
async def summarize(task_input: SummarizeTaskInput) -> SummarizeTaskOutput:
    """Use bullet points"""
    ...


async def test_summarize():
    summarized = await summarize(SummarizeTaskInput(text="Hello, world!"))
    assert summarized.summary
