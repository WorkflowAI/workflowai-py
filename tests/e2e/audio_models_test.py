"""
This test verifies model availability for audio processing tasks.
It checks which models support audio processing and which don't,
ensuring proper handling of unsupported models.
"""

import base64
import os

import pytest
from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

import workflowai
from workflowai import Model, Run
from workflowai.fields import Audio


class AudioInput(BaseModel):
    """Input containing the audio file to analyze."""
    audio: Audio = Field(
        description="The audio recording to analyze for spam/robocall detection",
    )


class SpamIndicator(BaseModel):
    """A specific indicator that suggests the call might be spam."""
    description: str = Field(
        description="Description of the spam indicator found in the audio",
        examples=[
            "Uses urgency to pressure the listener",
            "Mentions winning a prize without entering a contest",
            "Automated/robotic voice detected",
        ],
    )
    quote: str = Field(
        description="The exact quote or timestamp where this indicator appears",
        examples=[
            "'You must act now before it's too late'",
            "'You've been selected as our prize winner'",
            "0:05-0:15 - Synthetic voice pattern detected",
        ],
    )


class AudioClassification(BaseModel):
    """Output containing the spam classification results."""
    is_spam: bool = Field(
        description="Whether the audio is classified as spam/robocall",
    )
    confidence_score: float = Field(
        description="Confidence score for the classification (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
    spam_indicators: list[SpamIndicator] = Field(
        default_factory=list,
        description="List of specific indicators that suggest this is spam",
    )
    reasoning: str = Field(
        description="Detailed explanation of why this was classified as spam or legitimate",
    )


@workflowai.agent(
    id="audio-spam-detector",
    model=Model.GEMINI_1_5_FLASH_LATEST,
)
async def classify_audio(audio_input: AudioInput) -> Run[AudioClassification]:
    """
    Analyze the audio recording to determine if it's a spam/robocall.

    Guidelines:
    1. Listen for common spam/robocall indicators:
       - Use of urgency or pressure tactics
       - Unsolicited offers or prizes
       - Automated/synthetic voices
       - Requests for personal/financial information
       - Impersonation of legitimate organizations

    2. Consider both content and delivery:
       - What is being said (transcribe key parts)
       - How it's being said (tone, pacing, naturalness)
       - Background noise and call quality

    3. Provide clear reasoning:
       - Cite specific examples from the audio
       - Explain confidence level
       - Note any uncertainty
    """
    ...


@pytest.fixture
def audio_file() -> Audio:
    """Load the test audio file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(current_dir, "assets", "call.mp3")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(
            f"Audio file not found at {audio_path}. "
            "Please make sure you have the example audio file in the correct location.",
        )

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    return Audio(
        content_type="audio/mp3",
        data=base64.b64encode(audio_data).decode(),
    )
