from unittest.mock import Mock

import pytest

from workflowai.core.client._utils import build_retryable_wait, split_chunks
from workflowai.core.domain.errors import BaseError, WorkflowAIError


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


class TestBuildRetryableWait:
    @pytest.fixture
    def request_error(self):
        response = Mock()
        response.headers = {"Retry-After": "0.01"}
        return WorkflowAIError(response=response, error=BaseError(message=""))

    async def test_should_retry_count(self, request_error: WorkflowAIError):
        should_retry, wait_for_exception = build_retryable_wait(60, 1)
        assert should_retry()
        await wait_for_exception(request_error)
        assert not should_retry()
