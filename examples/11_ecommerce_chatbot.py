"""
This example demonstrates how to create an e-commerce chatbot that:
1. Understands customer queries about products
2. Provides helpful responses with product recommendations
3. Maintains context through conversation using .reply
4. Returns structured product recommendations
"""

import asyncio
from typing import Optional

from pydantic import BaseModel, Field

import workflowai
from workflowai import Model


class Product(BaseModel):
    """Model representing a product recommendation."""

    name: str = Field(
        description="Name of the product",
        examples=["Wireless Noise-Cancelling Headphones", "4K Smart TV"],
    )
    price: float = Field(
        description="Price of the product in USD",
        examples=[299.99, 799.99],
        ge=0,
    )
    description: str = Field(
        description="Brief description of the product",
        examples=[
            "Premium wireless headphones with active noise cancellation",
            "65-inch 4K Smart TV with HDR support",
        ],
    )
    rating: Optional[float] = Field(
        default=None,
        description="Customer rating out of 5 stars",
        examples=[4.5, 4.8],
        ge=0,
        le=5,
    )
    url: Optional[str] = Field(
        default=None,
        description="URL to view the product details",
        examples=["https://example.com/products/wireless-headphones"],
    )


class AssistantMessage(BaseModel):
    """Model representing a message from the assistant."""

    content: str = Field(
        description="The content of the message",
    )
    recommended_products: Optional[list[Product]] = Field(
        default=None,
        description="Product recommendations included with this message, if any",
    )


class ChatbotOutput(BaseModel):
    """Output model for the chatbot response."""

    assistant_message: AssistantMessage = Field(
        description="The chatbot's response message",
    )


class ChatInput(BaseModel):
    """Input model containing the user's message."""

    user_message: str = Field(
        description="The current message from the user",
    )


@workflowai.agent(
    id="ecommerce-chatbot",
    model=Model.LLAMA_3_3_70B,
)
async def get_product_recommendations(chat_input: ChatInput) -> ChatbotOutput:
    """
    Act as a knowledgeable e-commerce shopping assistant.

    Guidelines:
    1. Understand customer needs and preferences:
       - Analyze the query for specific requirements (price range, features, etc.)
       - Consider any context from conversation history
       - Ask clarifying questions if needed

    2. Provide helpful recommendations:
       - Suggest 3-5 relevant products that match the criteria
       - Include a mix of price points when appropriate
       - Explain why each product is recommended

    3. Maintain a friendly, professional tone:
       - Be conversational but informative
       - Highlight key features and benefits
       - Acknowledge specific customer needs

    4. Product information should be realistic:
       - Use reasonable prices for the product category
       - Include accurate descriptions and features
       - Provide realistic ratings based on typical products

    5. Format the response clearly:
       - Start with a helpful message addressing the query
       - Follow with relevant product recommendations
       - Make it easy to understand the options
    """
    ...


async def main():
    # Example 1: Initial query about headphones
    print("\nExample 1: Looking for headphones")
    print("-" * 50)

    run = await get_product_recommendations.run(
        ChatInput(user_message="I'm looking for noise-cancelling headphones for travel. My budget is around $300."),
    )
    print(run)

    # Example 2: Follow-up question using reply
    print("\nExample 2: Follow-up about battery life")
    print("-" * 50)

    run = await run.reply(user_message="Which one has the best battery life?")
    print(run)

    # Example 3: Specific question about a previously recommended product
    print("\nExample 3: Question about a specific product")
    print("-" * 50)

    run = await run.reply(
        user_message=(
            "Tell me more about the noise cancellation features of the first headphone you recommended."
        ),
    )
    print(run)

    # Example 4: Different product category
    print("\nExample 4: Looking for a TV")
    print("-" * 50)

    run = await run.reply(user_message="I need a good TV for gaming. My budget is $1000.")
    print(run)


if __name__ == "__main__":
    asyncio.run(main())
