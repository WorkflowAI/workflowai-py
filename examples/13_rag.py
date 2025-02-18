"""
This example demonstrates how to create a RAG-enabled chatbot that:
1. Uses a search tool to find relevant information from a knowledge base
2. Incorporates search results into its responses
3. Maintains conversation context
4. Provides well-structured, informative responses

Note: WorkflowAI does not manage the RAG implementation (yet). You need to provide your own
search implementation to connect to your knowledge base. This example uses a mock search
function to demonstrate the pattern.
"""

import asyncio
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

import workflowai
from workflowai import Model, Run


class Role(str, Enum):
    """Enum representing possible message roles."""

    USER = "user"
    ASSISTANT = "assistant"


class SearchResult(BaseModel):
    """Model representing a search result from the knowledge base."""

    content: str = Field(
        description="The content of the search result",
    )
    relevance_score: float = Field(
        description="Score indicating how relevant this result is to the query",
    )


# Simulated knowledge base search tool
# ruff: noqa: ARG001
async def search_faq(query: str) -> list[SearchResult]:
    """
    Search the knowledge base for relevant information.

    Args:
        query: The search query to find relevant information

    Returns:
        A list of search results ordered by relevance
    """
    # This is a mock implementation - in a real system this would query your knowledge base
    # The results below are hardcoded but in a real implementation would be based on the query
    return [
        SearchResult(
            content=(
                "Our standard return policy allows returns within 30 days of purchase with original "
                "receipt. Items must be unused and in original packaging. Once received, refunds are "
                "processed within 5-7 business days."
            ),
            relevance_score=0.95,
        ),
        SearchResult(
            content=(
                "For online purchases, customers can initiate returns through their account dashboard "
                "or by contacting customer support. Free return shipping labels are provided for "
                "defective items."
            ),
            relevance_score=0.88,
        ),
        SearchResult(
            content=(
                "Standard shipping takes 3-5 business days within the continental US. Express shipping "
                "(1-2 business days) is available for an additional fee. Free shipping on orders over $50."
            ),
            relevance_score=0.82,
        ),
    ]


class Message(BaseModel):
    """Model representing a chat message."""

    role: Role
    content: str = Field(
        description="The content of the message",
    )


class AssistantMessage(Message):
    """Model representing a message from the assistant."""

    role: Role = Role.ASSISTANT
    content: str = ""


class ChatbotOutput(BaseModel):
    """Output model for the chatbot response."""

    assistant_message: AssistantMessage = Field(
        default_factory=AssistantMessage,
        description="The chatbot's response message",
    )


class ChatInput(BaseModel):
    """Input model containing the user's message and conversation history."""

    conversation_history: Optional[list[Message]] = Field(
        default=None,
        description="Previous messages in the conversation, if any",
    )
    user_message: str = Field(
        description="The current message from the user",
    )


@workflowai.agent(
    id="rag-chatbot",
    model=Model.CLAUDE_3_5_SONNET_LATEST,
    # The search_faq function is passed as a tool, allowing the agent to call it during execution.
    # You can replace this with your own search implementation that connects to your knowledge base.
    # The agent will automatically handle calling the tool and incorporating the results.
    tools=[search_faq],
)
async def chat_agent(chat_input: ChatInput) -> Run[ChatbotOutput]:
    """
    Act as a knowledgeable assistant that uses search to find and incorporate relevant information.

    You have access to a search tool that can find relevant information from the knowledge base.
    Use it by calling the search_faq function with your query.

    Guidelines:
    1. Understand the user's query:
       - Analyze the question and conversation history
       - Identify key concepts to search for
       - Consider context from previous messages

    2. Search effectively:
       - Use the search_faq tool to find relevant information
       - Construct focused search queries
       - Consider multiple searches if needed
       - Prioritize recent and authoritative sources

    3. Provide comprehensive responses:
       - Synthesize information from search results
       - Cite sources when appropriate
       - Explain complex concepts clearly
       - Address all parts of the query

    4. Maintain conversation flow:
       - Acknowledge previous context
       - Be natural and engaging
       - Ask clarifying questions if needed
       - Provide smooth transitions

    5. Format responses clearly:
       - Structure information logically
       - Use clear language
       - Break down complex answers
       - Highlight key points
    """
    ...


async def main():
    # Example: Question about return policy
    print("\nExample: Question about return policy")
    print("-" * 50)

    chat_input = ChatInput(
        user_message="What is your return policy? Can I return items I bought online?",
    )

    run = await chat_agent(chat_input)
    print(run)


if __name__ == "__main__":
    asyncio.run(main())
