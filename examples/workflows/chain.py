import asyncio
from typing import TypedDict

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

import workflowai
from workflowai import Model


class MarketingCopyInput(BaseModel):
    """The product or concept for which to generate marketing copy."""

    idea: str = Field(description="A short description or name of the product.")


class MarketingCopyOutput(BaseModel):
    """Contains the AI generated marketing copy text for the provided product or concept."""

    marketing_text: str = Field(description="Persuasive marketing copy text.")


@workflowai.agent(id="marketing-copy-generator", model=Model.GPT_4O_MINI_LATEST)
async def generate_marketing_copy_agent(_: MarketingCopyInput) -> MarketingCopyOutput:
    """
    Write persuasive marketing copy for the provided idea.
    Focus on benefits and emotional appeal.
    """
    ...


class EvaluateCopyInput(BaseModel):
    """Input type for evaluating the quality of marketing copy."""

    marketing_text: str = Field(description="The marketing copy text to evaluate.")


class EvaluateCopyOutput(BaseModel):
    """Evaluation results for the marketing copy."""

    has_call_to_action: bool = Field(description="Whether a call to action is present.")
    emotional_appeal: int = Field(description="Emotional appeal rating (1-10).")
    clarity: int = Field(description="Clarity rating (1-10).")


# We use a smarter model (O1) to review the copy since evaluation requires more nuanced understanding
@workflowai.agent(id="marketing-copy-evaluator", model=Model.O1_MINI_LATEST)
async def evaluate_marketing_copy_agent(_: EvaluateCopyInput) -> EvaluateCopyOutput:
    """
    Evaluate the marketing copy for:
      1) Presence of a call to action (true/false)
      2) Emotional appeal (1-10)
      3) Clarity (1-10)
    Return the results as a structured output.
    """
    ...


class RewriteCopyInput(BaseModel):
    """Input for rewriting the marketing copy with targeted improvements."""

    original_copy: str = Field(default="", description="Original marketing copy.")
    add_call_to_action: bool = Field(default=False, description="Whether we need a clear call to action.")
    strengthen_emotional_appeal: bool = Field(default=False, description="Whether emotional appeal needs a boost.")
    improve_clarity: bool = Field(default=False, description="Whether clarity needs improvement.")


class RewriteCopyOutput(BaseModel):
    """Contains the improved marketing copy."""

    marketing_text: str = Field(description="The improved marketing copy text.")


# Claude 3.5 Sonnet is a more powerful model for copywriting
@workflowai.agent(model=Model.CLAUDE_3_5_SONNET_LATEST)
async def rewrite_marketing_copy_agent(_: RewriteCopyInput) -> RewriteCopyOutput:
    """
    Rewrite the marketing copy with the specified improvements:
    - A clear CTA if requested
    - Stronger emotional appeal if requested
    - Improved clarity if requested
    """
    ...


class MarketingResult(TypedDict):
    original_copy: str
    final_copy: str
    was_improved: bool
    quality_metrics: EvaluateCopyOutput


async def generate_marketing_copy(idea: str) -> MarketingResult:
    """
    Demonstrates a chain flow:
      1) Generate an initial marketing copy.
      2) Evaluate its quality.
      3) If the quality is lacking, request a rewrite with clearer CTA, stronger emotional appeal, and/or clarity.
      4) Return the final copy and metrics.
    """
    # Step 1: Generate initial copy
    generation = await generate_marketing_copy_agent(MarketingCopyInput(idea=idea))
    original_copy = generation.marketing_text
    final_copy = original_copy

    # Step 2: Evaluate the copy
    evaluation = await evaluate_marketing_copy_agent(EvaluateCopyInput(marketing_text=original_copy))

    # Step 3: Check evaluation results. If below thresholds, rewrite
    needs_improvement = not evaluation.has_call_to_action or evaluation.emotional_appeal < 7 or evaluation.clarity < 7

    if needs_improvement:
        rewrite = await rewrite_marketing_copy_agent(
            RewriteCopyInput(
                original_copy=original_copy,
                add_call_to_action=not evaluation.has_call_to_action,
                strengthen_emotional_appeal=evaluation.emotional_appeal < 7,
                improve_clarity=evaluation.clarity < 7,
            ),
        )
        final_copy = rewrite.marketing_text

    return {
        "original_copy": original_copy,
        "final_copy": final_copy,
        "was_improved": needs_improvement,
        "quality_metrics": evaluation,
    }


if __name__ == "__main__":
    idea = "A open-source platform for AI agents"
    result = asyncio.run(generate_marketing_copy(idea))

    print("\n=== Input Idea ===")
    print(idea)

    print("\n=== Marketing Copy ===")
    print(result["original_copy"])

    print("\n=== Quality Assessment ===")
    metrics = result["quality_metrics"]
    print(f"✓ Call to Action: {'Present' if metrics.has_call_to_action else 'Missing'}")
    print(f"✓ Emotional Appeal: {metrics.emotional_appeal}/10")
    print(f"✓ Clarity: {metrics.clarity}/10")

    if result["was_improved"]:
        print("\n=== Improved Marketing Copy ===")
        print(result["final_copy"])
    print()
