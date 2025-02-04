from pydantic import BaseModel

from workflowai.core.domain.tool import Tool


class TestToolDefinition:
    def test_simple(self):
        def sample_func(name: str, age: int) -> str:
            """Hello I am a docstring"""
            return f"Hello {name}, you are {age} years old"

        tool = Tool.from_fn(sample_func)
        assert tool.name == "sample_func"
        assert tool.description == "Hello I am a docstring"
        assert tool.input_schema == {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        assert tool.output_schema == {"type": "string"}
        assert tool.input_deserializer is None
        assert tool.output_serializer is None
        assert tool.tool_fn == sample_func


class TestSanity:
    """Test that we can create a tool from a function and then call it from a serialized input"""

    async def test_simple_non_async(self):
        def sample_func(name: str, age: int) -> str:
            return f"Hello {name}, you are {age} years old"

        tool = Tool.from_fn(sample_func)

        assert await tool({"name": "John", "age": 30}) == "Hello John, you are 30 years old"

    async def test_simple_async(self):
        async def sample_func(name: str, age: int) -> str:
            return f"Hello {name}, you are {age} years old"

        tool = Tool.from_fn(sample_func)

        assert await tool({"name": "John", "age": 30}) == "Hello John, you are 30 years old"

    async def test_base_model_in_input(self):
        class TestModel(BaseModel):
            name: str

        def sample_func(model: TestModel) -> str:
            return f"Hello {model.name}"

        tool = Tool.from_fn(sample_func)

        assert await tool({"model": {"name": "John"}}) == "Hello John"

    async def test_base_model_in_output(self):
        class TestModel(BaseModel):
            name: str

        def sample_func() -> TestModel:
            return TestModel(name="John")

        tool = Tool.from_fn(sample_func)

        assert await tool({}) == {"name": "John"}
