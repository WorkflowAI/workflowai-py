import datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field

# A type alias for evaluation tags. Goal is to provide some basic commonly used values
EvaluationTags = Union[Literal["positive", "negative", "neutral"], str]

EvaluatorMetric = Literal["correctness", "latency", "cost", "quality", "faithfulness"]


class TaskEvaluation(BaseModel):
    score: float = Field(..., ge=0, le=1, description="The score of the evaluation")
    tags: Optional[list[EvaluationTags]] = Field(
        default=None,
        description="Metadata added by the evaluator",
    )

    comment: Optional[str] = Field(
        default=None,
        description="An optional comment from the evaluation",
    )

    class Evaluator(BaseModel):
        id: str = Field(
            ...,
            description="The id of the evaluator that computed the score. "
            "Only one score per id can be attached to a task run.",
            examples=["1.0", "user:1"],
        )
        name: str = Field(
            ...,
            description="The name of the evaluator that computed the score e-g 'equality' or 'user'",
        )
        properties: dict[str, Any]
        metric: EvaluatorMetric = Field(
            default="correctness",
            description="The metric that was used to compute the score",
        )

    evaluator: Evaluator = Field(
        ...,
        description="Information about the evaluator that computed the score",
    )

    created_at: datetime.datetime = Field(
        description="The time at which the score was created",
    )

    example_id: Optional[str] = Field(
        default=None,
        description="The id of the example that was used in the evaluation",
    )
