from enum import Enum
from typing import AsyncIterator, Optional

import pytest
from pydantic import BaseModel

import workflowai
from workflowai.core.client.agent import Agent
from workflowai.core.client.client import WorkflowAI


class ExtractProductReviewSentimentTaskInput(BaseModel):
    review_text: Optional[str] = None


class Sentiment(Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class ExtractProductReviewSentimentTaskOutput(BaseModel):
    sentiment: Optional[Sentiment] = None


@workflowai.agent(id="extract-product-review-sentiment", schema_id=1)
def extract_product_review_sentiment(
    task_input: ExtractProductReviewSentimentTaskInput,
) -> AsyncIterator[ExtractProductReviewSentimentTaskOutput]: ...


@pytest.fixture
def extract_product_review_sentiment_agent(
    wai: WorkflowAI,
) -> Agent[ExtractProductReviewSentimentTaskInput, ExtractProductReviewSentimentTaskOutput]:
    return Agent(
        agent_id="extract-product-review-sentiment",
        schema_id=1,
        input_cls=ExtractProductReviewSentimentTaskInput,
        output_cls=ExtractProductReviewSentimentTaskOutput,
        api=wai.api,
    )


async def test_run_task(
    extract_product_review_sentiment_agent: Agent[
        ExtractProductReviewSentimentTaskInput,
        ExtractProductReviewSentimentTaskOutput,
    ],
):
    task_input = ExtractProductReviewSentimentTaskInput(review_text="This product is amazing!")
    run = await extract_product_review_sentiment_agent.run(task_input=task_input, use_cache="never")
    assert run.task_output.sentiment == Sentiment.POSITIVE


async def test_stream_task(
    extract_product_review_sentiment_agent: Agent[
        ExtractProductReviewSentimentTaskInput,
        ExtractProductReviewSentimentTaskOutput,
    ],
):
    task_input = ExtractProductReviewSentimentTaskInput(
        review_text="This product is amazing!",
    )

    streamed = extract_product_review_sentiment_agent.stream(
        task_input=task_input,
        use_cache="never",
    )
    chunks = [chunk async for chunk in streamed]

    assert len(chunks) > 1
