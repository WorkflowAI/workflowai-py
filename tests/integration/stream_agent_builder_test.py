from collections.abc import AsyncIterator
from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]
from typing_extensions import TypeAlias

import workflowai
from tests.integration.conftest import IntTestClient
from workflowai.core.domain.model import Model


class ChatMessage(BaseModel):
    role: Literal["USER", "ASSISTANT"] = Field(
        description="The role of the message sender",
        examples=["USER", "ASSISTANT"],
    )
    content: str = Field(
        description="The content of the message",
        examples=[
            "Thank you for your help!",
            "What is the weather forecast for tomorrow?",
        ],
    )


class UserChatMessage(ChatMessage):
    role: Literal["USER", "ASSISTANT"] = "USER"


class AssistantChatMessage(ChatMessage):
    role: Literal["USER", "ASSISTANT"] = "ASSISTANT"


class Product(BaseModel):
    name: Optional[str] = None
    features: Optional[list[str]] = None
    description: Optional[str] = None
    target_users: Optional[list[str]] = None


class AgentSchemaJson(BaseModel):
    agent_name: str = Field(description="The name of the agent in Title Case", serialization_alias="task_name")
    input_json_schema: Optional[dict[str, Any]] = Field(
        default=None,
        description="The JSON schema of the agent input",
    )
    output_json_schema: Optional[dict[str, Any]] = Field(
        default=None,
        description="The JSON schema of the agent output",
    )


InputFieldType: TypeAlias = Optional[
    Union["InputGenericFieldConfig", "EnumFieldConfig", "InputArrayFieldConfig", "InputObjectFieldConfig"]
]

OutputFieldType: TypeAlias = Optional[
    Union[
        "OutputGenericFieldConfig",
        "OutputStringFieldConfig",
        "EnumFieldConfig",
        "OutputArrayFieldConfig",
        "OutputObjectFieldConfig",
    ]
]
InputItemType: TypeAlias = Optional[Union["EnumFieldConfig", "InputObjectFieldConfig", "InputGenericFieldConfig"]]
OutputItemType: TypeAlias = Optional[
    Union["OutputStringFieldConfig", "EnumFieldConfig", "OutputObjectFieldConfig", "OutputGenericFieldConfig"]
]


class InputSchemaFieldType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    AUDIO_FILE = "audio_file"
    IMAGE_FILE = "image_file"
    DOCUMENT_FILE = "document_file"  # Include various text formats, pdfs and images
    DATE = "date"
    DATETIME = "datetime"
    TIMEZONE = "timezone"
    URL = "url"
    EMAIL = "email"
    HTML = "html"


class OutputSchemaFieldType(Enum):
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    DATETIME_LOCAL = "datetime_local"
    TIMEZONE = "timezone"
    URL = "url"
    EMAIL = "email"
    HTML = "html"


class BaseFieldConfig(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="The name of the field, must be filled when the field is an object field",
    )
    description: Optional[str] = Field(default=None, description="The description of the field")


class InputGenericFieldConfig(BaseFieldConfig):
    type: Optional[InputSchemaFieldType] = Field(default=None, description="The type of the field")


class OutputStringFieldConfig(BaseFieldConfig):
    type: Literal["string"] = "string"
    examples: Optional[list[str]] = Field(default=None, description="The examples of the field")


class EnumFieldConfig(BaseFieldConfig):
    type: Literal["enum"] = "enum"
    values: Optional[list[str]] = Field(default=None, description="The possible values of the enum")


class InputObjectFieldConfig(BaseFieldConfig):
    type: Literal["object"] = "object"
    fields: list[InputFieldType] = Field(description="The fields of the object", default_factory=list)


class InputArrayFieldConfig(BaseFieldConfig):
    type: Literal["array"] = "array"
    item_type: InputItemType = Field(default=None, description="The type of the items in the array")


class OutputGenericFieldConfig(BaseFieldConfig):
    type: OutputSchemaFieldType = Field(default=None, description="The type of the field")


class OutputObjectFieldConfig(BaseFieldConfig):
    type: Literal["object"] = "object"
    fields: list[OutputFieldType] = Field(description="The fields of the object", default_factory=list)


class OutputArrayFieldConfig(BaseFieldConfig):
    type: Literal["array"] = "array"
    item_type: OutputItemType = Field(default=None, description="The type of the items in the array")


class AgentBuilderInput(BaseModel):
    previous_messages: list[ChatMessage] = Field(
        description="List of previous messages exchanged between the user and the assistant",
    )
    new_message: ChatMessage = Field(
        description="The new message received from the user, based on which the routing decision is made",
    )
    existing_agent_schema: Optional[AgentSchemaJson] = Field(
        default=None,
        description="The previous agent schema, to update, if any",
    )
    available_tools_description: Optional[str] = Field(
        default=None,
        description="The description of the available tools",
    )

    class UserContent(BaseModel):
        company_name: Optional[str] = None
        company_description: Optional[str] = None
        company_locations: Optional[list[str]] = None
        company_industries: Optional[list[str]] = None
        company_products: Optional[list[Product]] = None
        current_agents: Optional[list[str]] = Field(
            default=None,
            description="The list of existing agents for the company",
        )

    user_context: Optional[UserContent] = Field(
        default=None,
        description="The context of the user, to inform the decision about the new agents schema",
    )


class AgentSchemaField(BaseModel):
    agent_name: str = Field(description="The name of the agent in Title Case", default="")
    input_schema: Optional[InputObjectFieldConfig] = Field(description="The schema of the agent input", default=None)
    output_schema: Optional[OutputObjectFieldConfig] = Field(description="The schema of the agent output", default=None)


class AgentBuilderOutput(BaseModel):
    answer_to_user: str = Field(description="The answer to the user, after processing of the 'new_message'", default="")

    new_agent_schema: Optional[AgentSchemaField] = Field(
        description="The new agent schema, if any, after processing of the 'new_message'",
        default=None,
    )


@workflowai.agent(id="chattaskschemageneration", model=Model.CLAUDE_3_5_SONNET_LATEST)
def stream_agent_builder(_: AgentBuilderInput) -> AsyncIterator[AgentBuilderOutput]:
    """bla"""
    ...


async def test_input_payload(test_client: IntTestClient):
    builder_input = AgentBuilderInput(
        previous_messages=[
            ChatMessage(role="USER", content="Hello"),
            ChatMessage(role="ASSISTANT", content="Hello, how can I help you today?"),
        ],
        new_message=ChatMessage(
            role="USER",
            content="I want to create an agent that extracts the main colors from an image",
        ),
        existing_agent_schema=AgentSchemaJson(
            agent_name="extract_colors",
            input_json_schema={
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "The URL of the image to extract colors from",
                    },
                },
            },
            output_json_schema={
                "type": "object",
                "properties": {
                    "colors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The main colors of the image",
                    },
                },
            },
        ),
        available_tools_description="You can use the following tools to help you create the agent schema",
    )

    test_client.mock_register(task_id="chattaskschemageneration")
    test_client.mock_stream(
        task_id="chattaskschemageneration",
        outputs=[
            {"answer_to_user": "a"},
            {"answer_to_user": "hello"},
            {"answer_to_user": "hello", "new_agent_schema": {"agent_name": "extract_colors"}},
            {
                "answer_to_user": "hello",
                "new_agent_schema": {
                    "agent_name": "extract_colors",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "image_url": {
                                "type": "string",
                            },
                        },
                    },
                },
            },
            {
                "answer_to_user": "hello",
                "new_agent_schema": {
                    "agent_name": "extract_colors",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "image_url": {
                                "type": "string",
                            },
                        },
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "colors": {
                                "type": "array",
                            },
                        },
                    },
                },
            },
        ],
    )

    chunks = [c async for c in stream_agent_builder(builder_input)]
    assert len(chunks) == 6

    expected_version = {
        "instructions": "bla",
        "model": "claude-3-5-sonnet-latest",
    }

    expected_task_input = {
        "city": "Hello",
        "available_tools_description": "You can use the following tools to help you create the agent schema",
        "existing_agent_schema": {
            "input_json_schema": {
                "properties": {
                    "image_url": {
                        "description": "The URL of the image to extract colors from",
                        "type": "string",
                    },
                },
                "type": "object",
            },
            "output_json_schema": {
                "properties": {
                    "colors": {
                        "description": "The main colors of the image",
                        "items": {
                            "type": "string",
                        },
                        "type": "array",
                    },
                },
                "type": "object",
            },
            "task_name": "extract_colors",
        },
        "new_message": {
            "content": "I want to create an agent that extracts the main colors from an image",
            "role": "USER",
        },
        "previous_messages": [
            {
                "content": "Hello",
                "role": "USER",
            },
            {
                "content": "Hello, how can I help you today?",
                "role": "ASSISTANT",
            },
        ],
        "user_context": None,
    }

    test_client.check_request(
        task_id="chattaskschemageneration",
        task_input=expected_task_input,
        version=expected_version,
    )
