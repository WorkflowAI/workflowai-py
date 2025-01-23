from typing import Any

import pytest

from workflowai.core.domain.version_properties import VersionProperties


@pytest.mark.parametrize(
    "payload",
    [
        {"model": "gpt-4o-latest"},
        {"model": "gpt-4o-latest", "provider": "openai"},
        {"model": "whatever"},
    ],
)
def test_version_properties_validate(payload: dict[str, Any]):
    # Check that we don't raise an error
    assert VersionProperties.model_validate(payload)
