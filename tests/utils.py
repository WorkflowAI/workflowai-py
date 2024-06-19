import json
import os
from typing import Any
from unittest.mock import AsyncMock


def fixture_path(*components: str, relative: bool = False) -> str:
    p = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        *components,
    )
    if relative:
        return os.path.relpath(p)
    return p


def fixture_text(*components: str) -> str:
    with open(fixture_path(*components), "r") as f:
        return f.read()


def fixtures_json(*components: str, bson: bool = False) -> Any:
    with open(fixture_path(*components), "r") as f:
        return json.load(f)


def mock_aiter(*args: Any):
    mock = AsyncMock()
    mock.__aiter__.return_value = args
    return mock
