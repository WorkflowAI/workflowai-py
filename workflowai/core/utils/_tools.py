import contextlib
import inspect
from typing import Any, Callable, NamedTuple, Optional, get_type_hints

from pydantic import TypeAdapter

from workflowai.core.utils._schema_generator import JsonSchemaGenerator

ToolFunction = Callable[..., Any]


class SchemaDeserializer(NamedTuple):
    schema: dict[str, Any]
    serializer: Optional[Callable[[Any], Any]] = None
    deserializer: Optional[Callable[[Any], Any]] = None


def _get_type_schema(param_type: type):
    """Convert a Python type to its corresponding JSON schema type.

    Args:
        param_type: The Python type to convert

    Returns:
        A dictionary containing the JSON schema type definition
    """

    if param_type is str:
        return SchemaDeserializer({"type": "string"})

    if param_type is int:
        return SchemaDeserializer({"type": "integer"})

    if param_type is float:
        return SchemaDeserializer({"type": "number"})

    if param_type is bool:
        return SchemaDeserializer({"type": "boolean"})

    # Attempting to build a type adapter with pydantic
    with contextlib.suppress(Exception):
        adapter = TypeAdapter[Any](param_type)
        return SchemaDeserializer(
            schema=adapter.json_schema(schema_generator=JsonSchemaGenerator),
            deserializer=adapter.validate_python,  # pyright: ignore [reportUnknownLambdaType]
            serializer=lambda x: adapter.dump_python(x, mode="json"),  # pyright: ignore [reportUnknownLambdaType]
        )

    raise ValueError(f"Unsupported type: {param_type}")


def _schema_from_type_hint(param_type_hint: Any):
    param_type = param_type_hint.__origin__ if hasattr(param_type_hint, "__origin__") else param_type_hint
    if not isinstance(param_type, type):
        raise ValueError(f"Unsupported type: {param_type}")

    param_description = param_type_hint.__metadata__[0] if hasattr(param_type_hint, "__metadata__") else None
    param_schema = _get_type_schema(param_type)
    if param_description:
        param_schema.schema["description"] = param_description

    return param_schema


def _combine_deserializers(deserializers: dict[str, Callable[[Any], Any]]):
    def deserializer(_input: dict[str, Any]) -> dict[str, Any]:
        return {k: deserializers[k](v) if k in deserializers else v for k, v in _input.items()}

    return deserializer


def _build_input_schema(sig: inspect.Signature, type_hints: dict[str, Any]):
    input_schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
    deserializers: dict[str, Callable[[Any], Any]] = {}

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        out = _schema_from_type_hint(type_hints[param_name])

        if param.default is inspect.Parameter.empty:
            input_schema["required"].append(param_name)

        input_schema["properties"][param_name] = out.schema
        if out.deserializer:
            deserializers[param_name] = out.deserializer

    if not input_schema["properties"]:
        return SchemaDeserializer({})

    deserializer = _combine_deserializers(deserializers) if deserializers else None

    # No need to serialize the input
    return SchemaDeserializer(input_schema, deserializer=deserializer)


def _build_output_schema(type_hints: dict[str, Any]):
    return_type = type_hints.get("return")
    if not return_type:
        raise ValueError("Return type annotation is required")

    # No need to deserialize the output
    return _schema_from_type_hint(return_type)._replace(deserializer=None)


def tool_schema(func: Callable[..., Any]):
    sig = inspect.signature(func)
    type_hints = get_type_hints(func, include_extras=True)

    input_schema = _build_input_schema(sig, type_hints)
    output_schema = _build_output_schema(type_hints)

    return input_schema, output_schema
