import httpx
import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from workflowai.core.client.api import APIClient
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


async def test_stream_404(httpx_mock: HTTPXMock):
    class TestInputModel(BaseModel):
        test_input: str

    class TestOutputModel(BaseModel):
        test_output: str

    httpx_mock.add_response(status_code=404)

    client = APIClient(endpoint="https://blabla.com", api_key="test_api_key")

    try:
        async for _ in client.stream(
            method="GET",
            path="test_path",
            data=TestInputModel(test_input="test"),
            returns=TestOutputModel,
        ):
            pass
    except Exception as e:
        assert isinstance(e, httpx.HTTPStatusError)
        assert e.response.status_code == 404
        assert e.response.reason_phrase == "Not Found"
