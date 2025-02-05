"""Tests to verify that the code examples in the README.md work as expected."""

from collections.abc import AsyncIterator
from datetime import date
from typing import List

import pytest
from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

import workflowai
from workflowai import Model, Run


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
        description="List of positive feedback points, each with a supporting quote.",
    )
    negative_points: List[FeedbackPoint] = Field(
        default_factory=list,
        description="List of negative feedback points, each with a supporting quote.",
    )


@workflowai.agent(id="analyze-call-feedback", model=Model.GPT_4O_MINI_LATEST)
async def analyze_call_feedback(input: CallFeedbackInput) -> Run[CallFeedbackOutput]:
    """
    Analyze a customer feedback call transcript to extract key insights:
    1. Identify positive feedback points with supporting quotes
    2. Identify negative feedback points with supporting quotes
    3. Include timestamp/context for each point

    Be specific and objective in the analysis. Use exact quotes from the transcript.
    Maintain the customer's original wording in quotes.
    """
    ...


@pytest.mark.asyncio
async def test_call_feedback_analysis():
    """Test the call feedback analysis example from the README."""
    # Example transcript from README
    transcript = """
    [00:01:15] Customer: I've been using your software for about 3 months now, and I have to say the new dashboard feature is really impressive. It's saving me at least an hour each day on reporting.

    [00:02:30] Customer: However, I'm really frustrated with the export functionality. It crashed twice this week when I tried to export large reports, and I lost all my work.

    [00:03:45] Customer: On a positive note, your support team, especially Sarah, was very responsive when I reported the issue. She got back to me within minutes.

    [00:04:30] Customer: But I think the pricing for additional users is a bit steep compared to other solutions we looked at.
    """

    # Create input
    feedback_input = CallFeedbackInput(
        transcript=transcript,
        call_date=date(2024, 1, 15),
    )

    # Analyze the feedback
    run = await analyze_call_feedback(feedback_input)

    # Verify the run object has expected attributes
    assert run.output is not None
    assert run.model is not None
    assert run.cost_usd is not None
    assert run.duration_seconds is not None

    # Verify we got both positive and negative points
    assert len(run.output.positive_points) > 0
    assert len(run.output.negative_points) > 0

    # Verify each point has the required fields
    for point in run.output.positive_points + run.output.negative_points:
        assert point.point
        assert point.quote
        assert point.timestamp

    # Print the analysis for manual verification
    print("\nPositive Points:")
    for point in run.output.positive_points:
        print(f"\n• {point.point}")
        print(f'  Quote [{point.timestamp}]: "{point.quote}"')

    print("\nNegative Points:")
    for point in run.output.negative_points:
        print(f"\n• {point.point}")
        print(f'  Quote [{point.timestamp}]: "{point.quote}"')


@workflowai.agent(id="analyze-call-feedback-stream")
def analyze_call_feedback_stream(input: CallFeedbackInput) -> AsyncIterator[Run[CallFeedbackOutput]]:
    """Same as analyze_call_feedback but with streaming enabled."""
    ...


@pytest.mark.asyncio
async def test_streaming_example():
    """Test the streaming example from the README."""
    feedback_input = CallFeedbackInput(
        transcript="[00:01:15] Customer: The product is great!",
        call_date=date(2024, 1, 15),
    )

    last_chunk = None
    chunks_received = 0

    async for chunk in analyze_call_feedback_stream(feedback_input):
        # Verify each chunk has an output
        assert chunk.output is not None
        chunks_received += 1
        last_chunk = chunk

    # Verify we received at least one chunk
    assert chunks_received > 0

    # Verify the last chunk has cost and duration
    assert last_chunk is not None
    assert last_chunk.cost_usd is not None
    assert last_chunk.duration_seconds is not None
