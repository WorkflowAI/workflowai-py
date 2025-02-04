import workflowai
from workflowai import Model, Run
from pydantic import BaseModel, Field
import asyncio


class NameExtractionInput(BaseModel):
    """Input containing a sentence with a person's name."""
    sentence: str = Field(description="A sentence containing a person's name.")


class NameExtractionOutput(BaseModel):
    """Output containing the extracted first and last name."""
    first_name: str = Field(
        default="",
        description="The person's first name extracted from the sentence."
    )
    last_name: str = Field(
        default="",
        description="The person's last name extracted from the sentence."
    )


@workflowai.agent(id='name-extractor', model=Model.GPT_4O_MINI_LATEST)
async def extract_name(input: NameExtractionInput) -> Run[NameExtractionOutput]:
    """
    Extract a person's first and last name from a sentence.
    Be precise and consider cultural variations in name formats.
    If multiple names are present, focus on the most prominent one.
    """
    ...


async def main():
    # Example sentences to test
    sentences = [
        "My friend John Smith went to the store.",
        "Dr. Maria Garcia-Rodriguez presented her research.",
        "The report was written by James van der Beek last week.",
    ]
    
    for sentence in sentences:
        print(f"\nProcessing: {sentence}")
        
        # Initial extraction
        run = await extract_name(NameExtractionInput(sentence=sentence))
        
        print(f"Extracted: {run.output.first_name} {run.output.last_name}")
        
        # Double check with a simple confirmation
        run = await run.reply(user_response="Are you sure?")
        
        print("\nAfter double-checking:")
        print(f"Final extraction: {run.output.first_name} {run.output.last_name}")


if __name__ == "__main__":
    asyncio.run(main()) 