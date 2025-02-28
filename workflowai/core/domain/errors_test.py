from typing import Optional
from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from workflowai.core.domain.errors import (
    BaseError,
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


def test_workflow_ai_error_code():
    error = WorkflowAIError(
        response=Mock(),
        error=BaseError(
            message="test",
            status_code=404,
            code="object_not_found",
        ),
    )
    assert error.code == "object_not_found"


def test_workflow_ai_error_status_code():
    error = WorkflowAIError(
        response=Mock(),
        error=BaseError(
            message="test",
            status_code=404,
            code="object_not_found",
        ),
    )
    assert error.status_code == 404


def test_workflow_ai_error_message():
    error = WorkflowAIError(
        response=Mock(),
        error=BaseError(
            message="test",
            status_code=404,
            code="object_not_found",
        ),
    )
    assert error.message == "test"


def test_workflow_ai_error_details():
    error = WorkflowAIError(
        response=Mock(),
        error=BaseError(
            message="test",
            status_code=404,
            code="object_not_found",
            details={"test": "test"},
        ),
    )
    assert error.details == {"test": "test"}
