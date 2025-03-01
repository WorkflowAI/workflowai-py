from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]

import workflowai
from workflowai import Model, Run


class NameExtractionInput(BaseModel):
    """Input containing a sentence with a person's name."""

    sentence: str = Field(description="A sentence containing a person's name.")


class NameExtractionOutput(BaseModel):
    """Output containing the extracted first and last name."""

    first_name: str = Field(
        default="",
        description="The person's first name extracted from the sentence.",
    )
    last_name: str = Field(
        default="",
        description="The person's last name extracted from the sentence.",
    )


@workflowai.agent(id="name-extractor", model=Model.GPT_4O_MINI_LATEST)
async def extract_name(_: NameExtractionInput) -> Run[NameExtractionOutput]:
    """
    Extract a person's first and last name from a sentence.
    Be precise and consider cultural variations in name formats.
    If multiple names are present, focus on the most prominent one.
    """
    ...


async def test_reply():
    run = await extract_name(NameExtractionInput(sentence="My friend John Smith went to the store."))

    assert run.output.first_name == "John"
    assert run.output.last_name == "Smith"

    run = await run.reply(user_message="Are you sure?")

    assert run.output.first_name == "John"
    assert run.output.last_name == "Smith"
