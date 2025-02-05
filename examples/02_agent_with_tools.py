"""
This example demonstrates how to use tools with WorkflowAI agents:
1. Built-in tools like @search-google
2. Custom tools (getting today's date and calculating days between dates)
3. Handling tool responses in the agent
"""

import asyncio
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field

import workflowai
from workflowai import Model, Run


def get_current_date() -> str:
    """Return today's date in ISO format (YYYY-MM-DD)"""
    return datetime.now().date().isoformat()


def calculate_days_between(
    date1: Annotated[str, "First date in YYYY-MM-DD format"],
    date2: Annotated[str, "Second date in YYYY-MM-DD format"],
) -> int:
    """Calculate the number of days between two dates."""
    d1 = date.fromisoformat(date1)
    d2 = date.fromisoformat(date2)
    return abs((d2 - d1).days)


class EventInput(BaseModel):
    """Input for finding information about an event."""
    query: str = Field(
        description="The event to get information about",
        examples=["When was the first iPhone released?", "Who won the 2022 World Cup?"],
    )


class EventOutput(BaseModel):
    """Output containing event information and context."""
    event_date: str = Field(
        description="The date when the event occurred",
        examples=["2007-06-29", "2022-12-18"],
    )
    description: str = Field(
        description="Description of the event",
    )
    days_since: int = Field(
        description="Number of days between the event and today",
    )
    source: str = Field(
        description="Source of the information",
    )


@workflowai.agent(
    id="event-analyzer",
    model=Model.GEMINI_1_5_FLASH_LATEST,
    tools=[get_current_date, calculate_days_between],
)
async def analyze_event(query: EventInput) -> Run[EventOutput]:
    """
    Find information about historical events and calculate days since they occurred.
    
    You have access to these tools:
    1. @search-google - Use this to find accurate information about events
    2. get_current_date - Use this to get today's date for calculating days since the event
    3. calculate_days_between - Calculate days between two dates (format: YYYY-MM-DD)
    
    Guidelines:
    1. Use @search-google to find accurate event information
    2. Get today's date using the get_current_date tool
    3. Use calculate_days_between with the event date and current date to get days_since
    4. Include the source of information (website URL)
    5. Be precise with dates and calculations
    6. Make sure dates are in YYYY-MM-DD format when using tools
    """
    ...


async def main():
    # Example 1: Recent tech launch event
    print("\nExample 1: Latest iPhone Launch")
    print("-" * 50)
    result = await analyze_event(EventInput(query="When was the latest iPhone launched?"))
    print(result.output)
    print(f"Cost: ${result.cost_usd}")
    print(f"Latency: {result.duration_seconds:.2f}s")

    # Example 2: Recent space exploration event
    print("\nExample 2: SpaceX Starship Launch")
    print("-" * 50)
    result = await analyze_event(EventInput(query="When was the latest SpaceX Starship test flight?"))
    print(result.output)
    print(f"Cost: ${result.cost_usd}")
    print(f"Latency: {result.duration_seconds:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
