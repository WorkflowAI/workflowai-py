from typing import Optional

from pydantic import BaseModel

import workflowai


class SummarizeTaskInput(BaseModel):
    text: Optional[str] = None


class SummarizeTaskOutput(BaseModel):
    summary_points: Optional[list[str]] = None


@workflowai.agent(id="summarize", model="gemini-1.5-flash-latest")
async def summarize(_: SummarizeTaskInput) -> SummarizeTaskOutput: ...


async def test_summarize():
    summarized = await summarize(
        SummarizeTaskInput(
            text="""The first computer programmer was Ada Lovelace. She wrote the first algorithm
intended to be processed by a machine in the 1840s. Her work was on Charles Babbage's
proposed mechanical computer, the Analytical Engine. She is celebrated annually on Ada
Lovelace Day, which promotes women in science and technology.""",
        ),
        use_cache="never",
    )
    assert summarized.summary_points
