from enum import Enum
from typing import Annotated

from pydantic import BaseModel

from workflowai.core.utils._tools import tool_schema


class TestToolSchema:
    def test_function_with_basic_types(self):
        class TestMode(str, Enum):
            FAST = "fast"
            SLOW = "slow"

        def sample_func(
            name: Annotated[str, "The name parameter"],
            age: int,
            height: float,
            is_active: bool,
            mode: TestMode = TestMode.FAST,
        ) -> bool:
            """Sample function for testing"""
            ...

        input_schema, output_schema = tool_schema(sample_func)

        assert input_schema.schema == {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name parameter",
                },
                "age": {
                    "type": "integer",
                },
                "height": {
                    "type": "number",
                },
                "is_active": {
                    "type": "boolean",
                },
                "mode": {
                    "type": "string",
                    "enum": ["fast", "slow"],
                },
            },
            "required": ["name", "age", "height", "is_active"],  # 'mode' is not required
        }
        assert output_schema.schema == {
            "type": "boolean",
        }

    def test_method_with_self(self):
        class TestClass:
            def sample_method(self, value: int) -> str:
                return str(value)

        input_schema, output_schema = tool_schema(TestClass.sample_method)

        assert input_schema.schema == {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                },
            },
            "required": ["value"],
        }
        assert output_schema.schema == {
            "type": "string",
        }

    def test_with_base_model_in_input(self):
        class TestModel(BaseModel):
            name: str

        def sample_func(model: TestModel) -> str: ...

        input_schema, output_schema = tool_schema(sample_func)

        assert input_schema.schema == {
            "type": "object",
            "properties": {
                "model": {
                    "properties": {
                        "name": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "name",
                    ],
                    "type": "object",
                },
            },
            "required": ["model"],
        }

        assert input_schema.deserializer is not None
        assert input_schema.deserializer({"model": {"name": "John"}}) == {"model": TestModel(name="John")}

        assert output_schema.schema == {
            "type": "string",
        }
        assert output_schema.deserializer is None

    def test_with_base_model_in_output(self):
        class TestModel(BaseModel):
            val: int

        def sample_func() -> TestModel: ...

        input_schema, output_schema = tool_schema(sample_func)

        assert input_schema.schema == {}
        assert input_schema.deserializer is None

        assert output_schema.schema == {
            "type": "object",
            "properties": {"val": {"type": "integer"}},
            "required": ["val"],
        }
        assert output_schema.serializer is not None
        assert output_schema.serializer(TestModel(val=10)) == {"val": 10}
