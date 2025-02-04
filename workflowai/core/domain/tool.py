import inspect
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from pydantic import BaseModel, Field

from workflowai.core.utils._tools import tool_schema


class ToolDefinition(BaseModel):
    name: str = Field(description="The name of the tool")
    description: str = Field(default="", description="The description of the tool")

    input_schema: dict[str, Any] = Field(description="The input class of the tool")
    output_schema: dict[str, Any] = Field(description="The output class of the tool")


ToolFunction = Callable[..., Any]


class Tool(ToolDefinition):
    input_deserializer: Optional[Callable[[Any], Any]] = Field(
        default=None,
        description="The deserializer for the input class of the tool",
    )

    output_serializer: Optional[Callable[[Any], Any]] = Field(
        default=None,
        description="The serializer for the output class of the tool",
    )

    tool_fn: Callable[..., Any] = Field(description="The function that implements the tool")

    @classmethod
    def from_fn(cls, func: ToolFunction):
        """Creates JSON schemas for function input parameters and return type.

        Args:
            func (Callable[[Any], Any]): a Python callable with annotated types

        Returns:
            FunctionJsonSchema: a FunctionJsonSchema object containing the function input/output JSON schemas
        """

        tool_description = inspect.getdoc(func)
        input_schema, output_schema = tool_schema(func)
        return cls(
            name=func.__name__,
            description=tool_description or "",
            input_schema=input_schema.schema,
            input_deserializer=input_schema.deserializer,
            output_schema=output_schema.schema,
            output_serializer=output_schema.serializer,
            tool_fn=func,
        )

    async def __call__(self, tool_input: Any):
        deserialized_input = self.input_deserializer(tool_input) if self.input_deserializer else tool_input
        if not deserialized_input:
            deserialized_input = {}
        output: Any = self.tool_fn(**deserialized_input)
        if isinstance(output, Awaitable):
            output = await output
        if self.output_serializer:
            return self.output_serializer(output)
        return output
