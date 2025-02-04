import asyncio
from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

import workflowai
from workflowai import Model


class QueryType(str, Enum):
    GENERAL = "general"
    REFUND = "refund"
    TECHNICAL = "technical"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"


class ClassificationInput(BaseModel):
    """Input for query classification."""

    query: str = Field(description="The customer query to classify.")


class ClassificationOutput(BaseModel):
    """Output containing query classification details."""

    reasoning: str = Field(description="Brief reasoning for the classification.")
    type: QueryType = Field(description="Type of the query (general, refund, or technical).")
    complexity: ComplexityLevel = Field(description="Complexity level of the query.")


# Uses GPT-4O for its strong analytical and classification capabilities
@workflowai.agent(id="query-classifier", model=Model.GPT_4O_LATEST)
async def classify_query_agent(
    _: ClassificationInput,
) -> ClassificationOutput:
    """
    Classify the customer query by:
    1. Query type (general, refund, or technical)
    2. Complexity (simple or complex)
    3. Provide brief reasoning for classification
    """
    ...


class ResponseInput(BaseModel):
    """Input for generating customer response."""

    query: str = Field(description="The customer query to respond to.")
    query_type: QueryType = Field(description="Type of the query for specialized handling.")


class ResponseOutput(BaseModel):
    """Output containing the response to the customer."""

    response: str = Field(description="The generated response to the customer query.")


# Uses Claude 3.5 Sonnet for its strong conversational abilities and empathy
@workflowai.agent(model=Model.CLAUDE_3_5_SONNET_LATEST)
async def handle_general_query(_: ResponseInput) -> ResponseOutput:
    """Expert customer service agent handling general inquiries."""
    ...


# Uses GPT-4O Mini for efficient policy-based responses
@workflowai.agent(model=Model.GPT_4O_MINI_LATEST)
async def handle_refund_query(_: ResponseInput) -> ResponseOutput:
    """Customer service agent specializing in refund requests."""
    ...


# Uses O1 Mini for its technical expertise and problem-solving capabilities
@workflowai.agent(model=Model.O1_MINI_LATEST)
async def handle_technical_query(_: ResponseInput) -> ResponseOutput:
    """Technical support specialist providing troubleshooting assistance."""
    ...


class QueryResult(TypedDict):
    response: str
    classification: ClassificationOutput


async def handle_customer_query(query: str) -> QueryResult:
    """
    Handle a customer query through a workflow:
    1. Classify the query type and complexity
    2. Route to appropriate specialized agent
    3. Return response and classification details
    """
    # Step 1: Classify the query
    classification = await classify_query_agent(ClassificationInput(query=query))

    # Step 2: Route to appropriate handler based on type and complexity
    handlers = {
        (QueryType.GENERAL, ComplexityLevel.SIMPLE): handle_general_query,
        (QueryType.GENERAL, ComplexityLevel.COMPLEX): handle_general_query,
        (QueryType.REFUND, ComplexityLevel.SIMPLE): handle_refund_query,
        (QueryType.REFUND, ComplexityLevel.COMPLEX): handle_refund_query,
        (QueryType.TECHNICAL, ComplexityLevel.SIMPLE): handle_technical_query,
        (QueryType.TECHNICAL, ComplexityLevel.COMPLEX): handle_technical_query,
    }

    # Get appropriate handler
    handler = handlers[(classification.type, classification.complexity)]

    # Generate response
    result = await handler(
        ResponseInput(
            query=query,
            query_type=classification.type,
        ),
    )

    return {
        "response": result.response,
        "classification": classification,
    }


if __name__ == "__main__":
    query = "I'm having trouble logging into my account."
    " It keeps saying invalid password even though I'm sure it's correct."
    result = asyncio.run(handle_customer_query(query))

    print("\n=== Customer Query ===")
    print(query)

    print("\n=== Classification ===")
    print(f"Type: {result['classification'].type}")
    print(f"Complexity: {result['classification'].complexity}")
    print(f"Reasoning: {result['classification'].reasoning}")

    print("\n=== Response ===")
    print(result["response"])
    print()
