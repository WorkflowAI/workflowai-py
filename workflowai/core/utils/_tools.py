import inspect
from enum import Enum
from typing import Any, Callable, get_type_hints

from pydantic import BaseModel

from workflowai.core.utils._schema_generator import JsonSchemaGenerator

ToolFunction = Callable[..., Any]


def tool_schema(func: ToolFunction):
    """Creates JSON schemas for function input parameters and return type.

    Args:
        func (Callable[[Any], Any]): a Python callable with annotated types

    Returns:
        FunctionJsonSchema: a FunctionJsonSchema object containing the function input/output JSON schemas
    """
    from workflowai.core.domain.tool import Tool

    sig = inspect.signature(func)
    type_hints = get_type_hints(func, include_extras=True)

    input_schema = _build_input_schema(sig, type_hints)
    output_schema = _build_output_schema(type_hints)

    tool_description = inspect.getdoc(func)

    return Tool(
        name=func.__name__,
        description=tool_description or "",
        input_schema=input_schema,
        output_schema=output_schema,
    )


def _get_type_schema(param_type: type) -> dict[str, Any]:
    """Convert a Python type to its corresponding JSON schema type.

    Args:
        param_type: The Python type to convert

    Returns:
        A dictionary containing the JSON schema type definition
    """
    if issubclass(param_type, Enum):
        if not issubclass(param_type, str):
            raise ValueError(f"Non string enums are not supported: {param_type}")
        return {"type": "string", "enum": [e.value for e in param_type]}

    if param_type is str:
        return {"type": "string"}

    if param_type in (int, float):
        return {"type": "number"}

    if param_type is bool:
        return {"type": "boolean"}

    if issubclass(param_type, BaseModel):
        return param_type.model_json_schema(by_alias=True, schema_generator=JsonSchemaGenerator)

    raise ValueError(f"Unsupported type: {param_type}")


def _schema_from_type_hint(param_type_hint: Any) -> dict[str, Any]:
    param_type = param_type_hint.__origin__ if hasattr(param_type_hint, "__origin__") else param_type_hint
    if not isinstance(param_type, type):
        raise ValueError(f"Unsupported type: {param_type}")

    param_description = param_type_hint.__metadata__[0] if hasattr(param_type_hint, "__metadata__") else None
    param_schema = _get_type_schema(param_type)
    if param_description:
        param_schema["description"] = param_description

    return param_schema


def _build_input_schema(sig: inspect.Signature, type_hints: dict[str, Any]) -> dict[str, Any]:
    input_schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        param_schema = _schema_from_type_hint(type_hints[param_name])

        if param.default is inspect.Parameter.empty:
            input_schema["required"].append(param_name)

        input_schema["properties"][param_name] = param_schema

    return input_schema


def _build_output_schema(type_hints: dict[str, Any]) -> dict[str, Any]:
    return_type = type_hints.get("return")
    if not return_type:
        raise ValueError("Return type annotation is required")

    return _schema_from_type_hint(return_type)
