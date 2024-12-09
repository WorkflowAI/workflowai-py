from typing import Optional
from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from workflowai.core.domain.errors import (
    WorkflowAIError,
    _retry_after_to_delay_seconds,  # pyright: ignore [reportPrivateUsage]
)


def test_workflow_ai_error_404():
    response = Mock()
    response.status_code = 404
    response.json = Mock()
    response.json.return_value = {"error": {"message": "None", "status_code": 404, "code": "object_not_found"}}

    error = WorkflowAIError.from_response(response)
    assert error.error.message == "None"
    assert error.error.status_code == 404
    assert error.error.code == "object_not_found"


@freeze_time("2024-01-01T00:00:00Z")
@pytest.mark.parametrize(
    ("retry_after", "expected"),
    [
        (None, None),
        ("10", 10),
        ("Wed, 01 Jan 2024 00:00:10 UTC", 10),
    ],
)
def test_retry_after_to_delay_seconds(retry_after: Optional[str], expected: Optional[float]):
    assert _retry_after_to_delay_seconds(retry_after) == expected
