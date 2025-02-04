import asyncio
from enum import Enum
from typing import List, TypedDict

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

import workflowai
from workflowai import Model


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SecurityReviewInput(BaseModel):
    """Input for security code review."""

    code: str = Field(description="The code to review for security issues.")


class SecurityReviewOutput(BaseModel):
    """Output from security code review."""

    vulnerabilities: List[str] = Field(description="List of identified security vulnerabilities.")
    risk_level: RiskLevel = Field(description="Overall security risk level.")
    suggestions: List[str] = Field(description="Security improvement suggestions.")


# Uses Claude 3.5 Sonnet for its strong security analysis capabilities
@workflowai.agent(id="security-reviewer", model=Model.CLAUDE_3_5_SONNET_LATEST)
async def security_review_agent(_: SecurityReviewInput) -> SecurityReviewOutput:
    """
    Expert in code security.
    Focus on identifying security vulnerabilities, injection risks, and authentication issues.
    """
    ...


class PerformanceReviewInput(BaseModel):
    """Input for performance code review."""

    code: str = Field(description="The code to review for performance issues.")


class PerformanceReviewOutput(BaseModel):
    """Output from performance code review."""

    issues: List[str] = Field(description="List of identified performance issues.")
    impact: RiskLevel = Field(description="Impact level of performance issues.")
    optimizations: List[str] = Field(description="Performance optimization suggestions.")


# Uses O1 Mini for its expertise in performance optimization
@workflowai.agent(id="performance-reviewer", model=Model.O1_MINI_LATEST)
async def performance_review_agent(_: PerformanceReviewInput) -> PerformanceReviewOutput:
    """
    Expert in code performance.
    Focus on identifying performance bottlenecks, memory leaks, and optimization opportunities.
    """
    ...


class MaintainabilityReviewInput(BaseModel):
    """Input for maintainability code review."""

    code: str = Field(description="The code to review for maintainability issues.")


class MaintainabilityReviewOutput(BaseModel):
    """Output from maintainability code review."""

    concerns: List[str] = Field(description="List of maintainability concerns.")
    quality_score: int = Field(description="Code quality score (1-10).", ge=1, le=10)
    recommendations: List[str] = Field(description="Maintainability improvement recommendations.")


# Uses Claude 3.5 Sonnet for its strong code quality and readability analysis
@workflowai.agent(id="maintainability-reviewer", model=Model.CLAUDE_3_5_SONNET_LATEST)
async def maintainability_review_agent(_: MaintainabilityReviewInput) -> MaintainabilityReviewOutput:
    """
    Expert in code quality.
    Focus on code structure, readability, and adherence to best practices.
    """
    ...


class ReviewSummaryInput(BaseModel):
    """Input for review summary generation."""

    security_review: SecurityReviewOutput = Field(description="Security review results.")
    performance_review: PerformanceReviewOutput = Field(description="Performance review results.")
    maintainability_review: MaintainabilityReviewOutput = Field(description="Maintainability review results.")


class ReviewSummaryOutput(BaseModel):
    """Output containing the summarized review."""

    summary: str = Field(description="Concise summary of all reviews with key actions.")


# Uses O1 for its strong synthesis and summarization abilities
@workflowai.agent(id="review-summarizer", model=Model.O1_2024_12_17_HIGH_REASONING_EFFORT)
async def summarize_reviews_agent(_: ReviewSummaryInput) -> ReviewSummaryOutput:
    """
    Technical lead summarizing multiple code reviews.
    Synthesize review results into a concise summary with key actions.
    """
    ...


class CodeReviewResult(TypedDict):
    security_review: SecurityReviewOutput
    performance_review: PerformanceReviewOutput
    maintainability_review: MaintainabilityReviewOutput
    summary: str


async def parallel_code_review(code: str) -> CodeReviewResult:
    """
    Perform parallel code reviews using specialized agents:
    1. Security review for vulnerabilities and risks
    2. Performance review for optimization opportunities
    3. Maintainability review for code quality
    4. Synthesize results into an actionable summary
    """
    # Run parallel reviews
    security_review, performance_review, maintainability_review = await asyncio.gather(
        security_review_agent(SecurityReviewInput(code=code)),
        performance_review_agent(PerformanceReviewInput(code=code)),
        maintainability_review_agent(MaintainabilityReviewInput(code=code)),
    )

    # Aggregate and summarize results
    summary = await summarize_reviews_agent(
        ReviewSummaryInput(
            security_review=security_review,
            performance_review=performance_review,
            maintainability_review=maintainability_review,
        ),
    )

    return {
        "security_review": security_review,
        "performance_review": performance_review,
        "maintainability_review": maintainability_review,
        "summary": summary.summary,
    }


if __name__ == "__main__":
    # Example code to review
    code_to_review = """
    def process_user_input(user_input):
        # Execute the input as a command
        result = eval(user_input)
        return result

    def cache_data(data):
        # Store everything in memory
        global_cache.append(data)

    def get_user_data(user_id):
        # Query without parameterization
        cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
        return cursor.fetchall()
    """

    result = asyncio.run(parallel_code_review(code_to_review))

    print("\n=== Security Review ===")
    print(f"Risk Level: {result['security_review'].risk_level}")
    print("\nVulnerabilities:")
    for v in result["security_review"].vulnerabilities:
        print(f"- {v}")
    print("\nSuggestions:")
    for s in result["security_review"].suggestions:
        print(f"- {s}")

    print("\n=== Performance Review ===")
    print(f"Impact Level: {result['performance_review'].impact}")
    print("\nIssues:")
    for i in result["performance_review"].issues:
        print(f"- {i}")
    print("\nOptimizations:")
    for o in result["performance_review"].optimizations:
        print(f"- {o}")

    print("\n=== Maintainability Review ===")
    print(f"Quality Score: {result['maintainability_review'].quality_score}/10")
    print("\nConcerns:")
    for c in result["maintainability_review"].concerns:
        print(f"- {c}")
    print("\nRecommendations:")
    for r in result["maintainability_review"].recommendations:
        print(f"- {r}")

    print("\n=== Summary ===")
    print(result["summary"])
    print()
