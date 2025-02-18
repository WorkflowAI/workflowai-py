import json
from datetime import datetime
from enum import Enum
from typing import Annotated, Any
from zoneinfo import ZoneInfo

import pytest
from pydantic import BaseModel

from workflowai.core.utils._tools import _get_type_schema, tool_schema  # pyright: ignore [reportPrivateUsage]


class TestGetTypeSchema:
    class _BasicEnum(str, Enum):
        A = "a"
        B = "b"

    class _BasicModel(BaseModel):
        a: int
        b: str

    @pytest.mark.parametrize(
        ("param_type", "value"),
        [
            (int, 1),
            (float, 1.0),
            (bool, True),
            (str, "test"),
            (datetime, datetime.now(tz=ZoneInfo("UTC"))),
            (ZoneInfo, ZoneInfo("UTC")),
            (list[int], [1, 2, 3]),
            (dict[str, int], {"a": 1, "b": 2}),
            (_BasicEnum, _BasicEnum.A),
            (_BasicModel, _BasicModel(a=1, b="test")),
            (list[_BasicModel], [_BasicModel(a=1, b="test"), _BasicModel(a=2, b="test2")]),
            (tuple[int, str], (1, "test")),
        ],
    )
    def test_get_type_schema(self, param_type: Any, value: Any):
        schema = _get_type_schema(param_type)
        if schema.serializer is None or schema.deserializer is None:
            assert schema.serializer is None
            assert schema.deserializer is None

            # Check that the value is serializable and deserializable with plain json
            assert json.loads(json.dumps(value)) == value
            return

        serialized = schema.serializer(value)
        deserialized = schema.deserializer(serialized)
        assert deserialized == value


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
            date: datetime,
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
                "date": {
                    "type": "string",
                    "format": "date-time",
                },
            },
            "required": ["name", "age", "height", "is_active", "date"],  # 'mode' is not required
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

    def test_with_datetime_in_input(self):
        def sample_func(time: datetime) -> str: ...

        input_schema, _ = tool_schema(sample_func)

        assert input_schema.deserializer is not None
        assert input_schema.deserializer({"time": "2024-01-01T12:00:00+00:00"}) == {
            "time": datetime(
                2024,
                1,
                1,
                12,
                0,
                0,
                tzinfo=ZoneInfo("UTC"),
            ),
        }
