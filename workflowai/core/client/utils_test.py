from typing import Optional
from unittest.mock import Mock

import pytest
from freezegun import freeze_time
from httpx import HTTPStatusError

from workflowai.core.client.utils import build_retryable_wait, retry_after_to_delay_seconds, split_chunks
from workflowai.core.domain.errors import WorkflowAIError


@pytest.mark.parametrize(
    ("chunk", "expected"),
    [
        (b'data: {"foo": "bar"}\n\ndata: {"foo": "baz"}', ['{"foo": "bar"}', '{"foo": "baz"}']),
        (
            b'data: {"foo": "bar"}\n\ndata: {"foo": "baz"}\n\ndata: {"foo": "qux"}',
            ['{"foo": "bar"}', '{"foo": "baz"}', '{"foo": "qux"}'],
        ),
    ],
)
def test_split_chunks(chunk: bytes, expected: list[bytes]):
    assert list(split_chunks(chunk)) == expected


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
    assert retry_after_to_delay_seconds(retry_after) == expected


class TestBuildRetryableWait:
    @pytest.fixture()
    def request_error(self):
        response = Mock()
        response.headers = {"Retry-After": "0.01"}
        return HTTPStatusError(message="", request=Mock(), response=response)

    async def test_should_retry_count(self, request_error: WorkflowAIError):
        should_retry, wait_for_exception = build_retryable_wait(60, 1)
        assert should_retry()
        await wait_for_exception(request_error)
        assert not should_retry()
