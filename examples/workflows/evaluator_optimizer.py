import asyncio
from typing import TypedDict

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

import workflowai
from workflowai import Model


class TranslationInput(BaseModel):
    """Input for translation."""

    text: str = Field(description="The text to translate.")
    target_language: str = Field(description="The target language for translation.")


class TranslationOutput(BaseModel):
    """Output containing the translated text."""

    translation: str = Field(description="The translated text.")


# Uses GPT-4O Mini for fast initial translation
@workflowai.agent(id="initial-translator", model=Model.GPT_4O_MINI_LATEST)
async def initial_translation_agent(_: TranslationInput) -> TranslationOutput:
    """
    Expert literary translator.
    Translate text while preserving tone and cultural nuances.
    """
    ...


class TranslationEvaluationInput(BaseModel):
    """Input for evaluating translation quality."""

    original_text: str = Field(description="The original text.")
    translation: str = Field(description="The translation to evaluate.")
    target_language: str = Field(description="The target language of the translation.")


class TranslationEvaluationOutput(BaseModel):
    """Output containing the translation evaluation."""

    quality_score: int = Field(description="Overall quality score (1-10).")
    preserves_tone: bool = Field(description="Whether the translation preserves the original tone.")
    preserves_nuance: bool = Field(description="Whether the translation preserves subtle nuances.")
    culturally_accurate: bool = Field(description="Whether the translation is culturally appropriate.")
    specific_issues: list[str] = Field(description="List of specific issues identified.")
    improvement_suggestions: list[str] = Field(description="List of suggested improvements.")


# Uses O1 for its strong analytical and evaluation capabilities
@workflowai.agent(id="translation-evaluator", model=Model.O1_2024_12_17_HIGH_REASONING_EFFORT)
async def evaluate_translation_agent(_: TranslationEvaluationInput) -> TranslationEvaluationOutput:
    """
    Expert in evaluating literary translations.
    Evaluate translations for quality, tone preservation, nuance, and cultural accuracy.
    """
    ...


class TranslationImprovementInput(BaseModel):
    """Input for improving translation based on feedback."""

    original_text: str = Field(description="The original text.")
    current_translation: str = Field(description="The current translation.")
    target_language: str = Field(description="The target language.")
    specific_issues: list[str] = Field(description="Issues to address.")
    improvement_suggestions: list[str] = Field(description="Suggestions for improvement.")


class TranslationImprovementOutput(BaseModel):
    """Output containing the improved translation."""

    translation: str = Field(description="The improved translation.")


# Uses GPT-4O for high-quality translation refinement
@workflowai.agent(id="translation-improver", model=Model.GPT_4O_LATEST)
async def improve_translation_agent(_: TranslationImprovementInput) -> TranslationImprovementOutput:
    """
    Expert literary translator.
    Improve translations based on specific feedback while maintaining overall quality.
    """
    ...


class TranslationResult(TypedDict):
    final_translation: str
    iterations_required: int


async def translate_with_feedback(text: str, target_language: str) -> TranslationResult:
    """
    Translate text with iterative feedback and improvement:
    1. Generate initial translation with a faster model
    2. Evaluate translation quality
    3. If quality threshold not met, improve based on feedback
    4. Repeat evaluation-improvement cycle up to max_iterations
    """
    max_iterations = 3
    iterations = 0

    # Initial translation using faster model
    current_translation = await initial_translation_agent(
        TranslationInput(
            text=text,
            target_language=target_language,
        ),
    )

    while iterations < max_iterations:
        # Evaluate current translation
        evaluation = await evaluate_translation_agent(
            TranslationEvaluationInput(
                original_text=text,
                translation=current_translation.translation,
                target_language=target_language,
            ),
        )

        # Check if quality meets threshold
        if (
            evaluation.quality_score >= 8
            and evaluation.preserves_tone
            and evaluation.preserves_nuance
            and evaluation.culturally_accurate
        ):
            break

        # Generate improved translation based on feedback
        improved = await improve_translation_agent(
            TranslationImprovementInput(
                original_text=text,
                current_translation=current_translation.translation,
                target_language=target_language,
                specific_issues=evaluation.specific_issues,
                improvement_suggestions=evaluation.improvement_suggestions,
            ),
        )

        current_translation.translation = improved.translation
        iterations += 1

    return {
        "final_translation": current_translation.translation,
        "iterations_required": iterations,
    }


if __name__ == "__main__":
    # Example text to translate
    text = """
    The old bookstore, nestled in the heart of the city,
    was a sanctuary for bibliophiles. Its wooden shelves,
    worn smooth by decades of searching hands, held stories
    in dozens of languages. The owner, a silver-haired woman
    with kind eyes, knew each book's location by heart.
    """
    target_language = "French"

    result = asyncio.run(translate_with_feedback(text, target_language))

    print("\n=== Translation Result ===")
    print("\nOriginal Text:")
    print(text)
    print("\nFinal Translation:")
    print(result["final_translation"])
    print(f"\nIterations Required: {result['iterations_required']}")
    print()
