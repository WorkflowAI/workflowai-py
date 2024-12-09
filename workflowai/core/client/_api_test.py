from collections.abc import Awaitable, Callable

import httpx
import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock, IteratorStream

from workflowai.core.client._api import APIClient
from workflowai.core.domain.errors import WorkflowAIError


class TestAPIClientExtractError:
    def test_extract_error(self):
        client = APIClient(endpoint="test_endpoint", api_key="test_api_key")

        # Test valid JSON error response
        response = httpx.Response(
            status_code=400,
            json={
                "error": {
                    "message": "Test error message",
                    "details": {"key": "value"},
                },
                "task_run_id": "test_task_123",
            },
        )

        error = client._extract_error(response, response.content)  # pyright:ignore[reportPrivateUsage]
        assert isinstance(error, WorkflowAIError)
        assert error.error.message == "Test error message"
        assert error.error.details == {"key": "value"}
        assert error.task_run_id == "test_task_123"
        assert error.response == response

    def test_extract_error_invalid_json(self):
        client = APIClient(endpoint="test_endpoint", api_key="test_api_key")

        # Test invalid JSON response
        invalid_data = b"Invalid JSON data"
        response = httpx.Response(status_code=400, content=invalid_data)

        with pytest.raises(WorkflowAIError) as e:
            client._extract_error(response, invalid_data)  # pyright:ignore[reportPrivateUsage]
        assert isinstance(e.value, WorkflowAIError)
        assert e.value.error.message == "Unknown error"
        assert e.value.error.details == {"raw": "b'Invalid JSON data'"}
        assert e.value.response == response

    def test_extract_error_with_custom_error(self):
        client = APIClient(endpoint="test_endpoint", api_key="test_api_key")

        # Test with provided exception
        invalid_data = "{'detail': 'Not Found'}"
        response = httpx.Response(status_code=404, content=invalid_data)
        exception = ValueError("Custom error")

        with pytest.raises(WorkflowAIError) as e:
            client._extract_error(response, invalid_data, exception)  # pyright:ignore[reportPrivateUsage]
        assert isinstance(e.value, WorkflowAIError)
        assert e.value.error.message == "Custom error"
        assert e.value.error.details == {"raw": "{'detail': 'Not Found'}"}
        assert e.value.response == response


@pytest.fixture
def client() -> APIClient:
    return APIClient(endpoint="https://blabla.com", api_key="test_api_key")


class TestInputModel(BaseModel):
    bla: str = "bla"


class TestOutputModel(BaseModel):
    a: str


class TestAPIClientStream:
    async def test_stream_404(self, httpx_mock: HTTPXMock, client: APIClient):
        class TestInputModel(BaseModel):
            test_input: str

        class TestOutputModel(BaseModel):
            test_output: str

        httpx_mock.add_response(status_code=404)

        with pytest.raises(WorkflowAIError) as e:  # noqa: PT012
            async for _ in client.stream(
                method="GET",
                path="test_path",
                data=TestInputModel(test_input="test"),
                returns=TestOutputModel,
            ):
                pass

        assert e.value.response
        assert e.value.response.status_code == 404
        assert e.value.response.reason_phrase == "Not Found"

    @pytest.fixture
    async def stream_fn(self, client: APIClient):
        async def _stm():
            return [
                chunk
                async for chunk in client.stream(
                    method="GET",
                    path="test_path",
                    data=TestInputModel(),
                    returns=TestOutputModel,
                )
            ]

        return _stm

    async def test_stream_with_single_chunk(
        self,
        stream_fn: Callable[[], Awaitable[list[TestOutputModel]]],
        httpx_mock: HTTPXMock,
    ):
        httpx_mock.add_response(
            stream=IteratorStream(
                [
                    b'data: {"a":"test"}\n\n',
                ],
            ),
        )

        chunks = await stream_fn()
        assert chunks == [TestOutputModel(a="test")]

    @pytest.mark.parametrize(
        "streamed_chunks",
        [
            # 2 perfect chunks([b'data: {"a":"test"}\n\n', b'data: {"a":"test2"}\n\n'],),
            [b'data: {"a":"test"}\n\n', b'data: {"a":"test2"}\n\n'],
            # 2 chunks in one
            [b'data: {"a":"test"}\n\ndata: {"a":"test2"}\n\n'],
            # Split not at the end
            [b'data: {"a":"test"}', b'\n\ndata: {"a":"test2"}\n\n'],
            # Really messy
            [b"dat", b'a: {"a":"', b'test"}', b"\n", b"\ndata", b': {"a":"test2"}\n\n'],
        ],
    )
    async def test_stream_with_multiple_chunks(
        self,
        stream_fn: Callable[[], Awaitable[list[TestOutputModel]]],
        httpx_mock: HTTPXMock,
        streamed_chunks: list[bytes],
    ):
        assert isinstance(streamed_chunks, list), "sanity check"
        assert all(isinstance(chunk, bytes) for chunk in streamed_chunks), "sanity check"

        httpx_mock.add_response(stream=IteratorStream(streamed_chunks))
        chunks = await stream_fn()
        assert chunks == [TestOutputModel(a="test"), TestOutputModel(a="test2")]
