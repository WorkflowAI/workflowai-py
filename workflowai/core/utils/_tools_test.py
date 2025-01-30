from enum import Enum
from typing import Annotated

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

        schema = tool_schema(sample_func)

        assert schema.name == "sample_func"
        assert schema.input_schema == {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name parameter",
                },
                "age": {
                    "type": "number",
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
        assert schema.output_schema == {
            "type": "boolean",
        }
        assert schema.description == "Sample function for testing"

    def test_method_with_self(self):
        class TestClass:
            def sample_method(self, value: int) -> str:
                return str(value)

        schema = tool_schema(TestClass.sample_method)

        assert schema.input_schema == {
            "type": "object",
            "properties": {
                "value": {
                    "type": "number",
                },
            },
            "required": ["value"],
        }
        assert schema.output_schema == {
            "type": "string",
        }
