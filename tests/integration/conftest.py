import json
from typing import Any, Optional
from unittest.mock import patch

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock, IteratorStream

from workflowai.core.client.client import WorkflowAI


@pytest.fixture(scope="module", autouse=True)
def init_client():
    with patch("workflowai.shared_client", new=WorkflowAI(api_key="test", endpoint="https://run.workflowai.dev")):
        yield


class CityToCapitalTaskInput(BaseModel):
    city: str


class CityToCapitalTaskOutput(BaseModel):
    capital: str


class IntTestClient:
    REGISTER_URL = "https://api.workflowai.dev/v1/_/agents"

    def __init__(self, httpx_mock: HTTPXMock):
        self.httpx_mock = httpx_mock

    def mock_register(self, schema_id: int = 1, task_id: str = "city-to-capital", variant_id: str = "1"):
        self.httpx_mock.add_response(
            method="POST",
            url=self.REGISTER_URL,
            json={"schema_id": schema_id, "variant_id": variant_id, "id": task_id},
        )

    def mock_response(
        self,
        task_id: str = "city-to-capital",
        capital: str = "Tokyo",
        json: Optional[dict[str, Any]] = None,
        url: Optional[str] = None,
        status_code: int = 200,
    ):
        self.httpx_mock.add_response(
            method="POST",
            url=url or f"https://run.workflowai.dev/v1/_/agents/{task_id}/schemas/1/run",
            json=json or {"id": "123", "task_output": {"capital": capital}},
            status_code=status_code,
        )

    def mock_stream(self, task_id: str = "city-to-capital"):
        self.httpx_mock.add_response(
            url=f"https://run.workflowai.dev/v1/_/agents/{task_id}/schemas/1/run",
            stream=IteratorStream(
                [
                    b'data: {"id":"1","task_output":{"capital":""}}\n\n',
                    b'data: {"id":"1","task_output":{"capital":"Tok"}}\n\ndata: {"id":"1","task_output":{"capital":"Tokyo"}}\n\n',  # noqa: E501
                    b'data: {"id":"1","task_output":{"capital":"Tokyo"},"cost_usd":0.01,"duration_seconds":10.1}\n\n',
                ],
            ),
        )

    def check_request(
        self,
        version: Any = "production",
        task_id: str = "city-to-capital",
        task_input: Optional[dict[str, Any]] = None,
        **matchers: Any,
    ):
        request = self.httpx_mock.get_request(**matchers)
        assert request is not None
        assert request.url == f"https://run.workflowai.dev/v1/_/agents/{task_id}/schemas/1/run"
        body = json.loads(request.content)
        assert body == {
            "task_input": task_input or {"city": "Hello"},
            "version": version,
            "stream": False,
        }
        assert request.headers["Authorization"] == "Bearer test"
        assert request.headers["Content-Type"] == "application/json"
        assert request.headers["x-workflowai-source"] == "sdk"
        assert request.headers["x-workflowai-language"] == "python"


@pytest.fixture
def test_client(httpx_mock: HTTPXMock) -> IntTestClient:
    return IntTestClient(httpx_mock)
