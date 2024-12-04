from enum import Enum
from typing import AsyncIterator, Optional

from pydantic import BaseModel

import workflowai
from workflowai.core.domain.task import Task


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


@workflowai.task(schema_id=1)
def extract_product_review_sentiment(
    task_input: ExtractProductReviewSentimentTaskInput,
) -> AsyncIterator[ExtractProductReviewSentimentTaskOutput]: ...


class ExtractProductReviewSentimentTask(
    Task[ExtractProductReviewSentimentTaskInput, ExtractProductReviewSentimentTaskOutput],
):
    id: str = "extract-product-review-sentiment"
    schema_id: int = 1
    input_class: type[ExtractProductReviewSentimentTaskInput] = ExtractProductReviewSentimentTaskInput
    output_class: type[ExtractProductReviewSentimentTaskOutput] = ExtractProductReviewSentimentTaskOutput


async def test_run_task(wai: workflowai.Client):
    task = ExtractProductReviewSentimentTask()
    task_input = ExtractProductReviewSentimentTaskInput(review_text="This product is amazing!")
    run = await wai.run(task, task_input=task_input, use_cache="never")
    assert run.task_output.sentiment == Sentiment.POSITIVE


async def test_stream_task(wai: workflowai.Client):
    task = ExtractProductReviewSentimentTask()

    task_input = ExtractProductReviewSentimentTaskInput(
        review_text="This product is amazing!",
    )

    streamed = await wai.run(task, task_input=task_input, stream=True, use_cache="never")
    chunks = [chunk async for chunk in streamed]

    assert len(chunks) > 1
