"""
This example demonstrates how to create a basic WorkflowAI agent that takes a city name
and returns information about the capital of its country. It showcases:

1. Basic agent creation with input/output models
2. Field descriptions and examples
3. Cost and latency tracking
"""

import asyncio

from pydantic import BaseModel, Field

import workflowai
from workflowai import Model, Run


class CityInput(BaseModel):
    """Input model for the city-to-capital agent."""
    city: str = Field(
        description="The name of the city for which to find the country's capital",
        examples=["Paris", "New York", "Tokyo"],
    )


class CapitalOutput(BaseModel):
    """Output model containing information about the capital city."""
    country: str = Field(
        description="The country where the input city is located",
        examples=["France", "United States", "Japan"],
    )
    capital: str = Field(
        description="The capital city of the country",
        examples=["Paris", "Washington D.C.", "Tokyo"],
    )
    fun_fact: str = Field(
        description="An interesting fact about the capital city",
        examples=["Paris has been the capital of France since 508 CE"],
    )


@workflowai.agent(
    id="city-to-capital",
    model=Model.CLAUDE_3_5_SONNET_LATEST,
)
async def get_capital_info(city_input: CityInput) -> Run[CapitalOutput]:
    """
    Find the capital city of the country where the input city is located.

    Guidelines:
    1. First identify the country where the input city is located
    2. Then provide the capital city of that country
    3. Include an interesting historical or cultural fact about the capital
    4. Be accurate and precise with geographical information
    5. If the input city is itself the capital, still provide the information
    """
    ...


async def main():
    # Example 1: Basic usage with Paris
    print("\nExample 1: Basic usage with Paris")
    print("-" * 50)
    run = await get_capital_info.run(CityInput(city="Paris"))
    print(run)

    # Example 2: Using Tokyo
    print("\nExample 2: Using Tokyo")
    print("-" * 50)
    run = await get_capital_info.runCityInput(city="Tokyo"))
    print(run)


if __name__ == "__main__":
    asyncio.run(main())
