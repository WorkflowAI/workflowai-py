import json
from typing import Any, AsyncIterator, Optional

from httpx import Request
from pydantic import BaseModel
from pytest_httpx import HTTPXMock, IteratorStream

import workflowai
from workflowai.core.domain.task_run import Run


class CityToCapitalTaskInput(BaseModel):
    city: str


class CityToCapitalTaskOutput(BaseModel):
    capital: str


workflowai.init(api_key="test", url="http://localhost:8000")


def _mock_response(httpx_mock: HTTPXMock, task_id: str = "city-to-capital"):
    httpx_mock.add_response(
        method="POST",
        url=f"http://localhost:8000/v1/_/tasks/{task_id}/schemas/1/run",
        json={"id": "123", "task_output": {"capital": "Tokyo"}},
    )


def _mock_stream(httpx_mock: HTTPXMock, task_id: str = "city-to-capital"):
    httpx_mock.add_response(
        url=f"http://localhost:8000/v1/_/tasks/{task_id}/schemas/1/run",
        stream=IteratorStream(
            [
                b'data: {"id":"1","task_output":{"capital":""}}\n\n',
                b'data: {"id":"1","task_output":{"capital":"Tok"}}\n\ndata: {"id":"1","task_output":{"capital":"Tokyo"}}\n\n',  # noqa: E501
                b'data: {"id":"1","task_output":{"capital":"Tokyo"},"cost_usd":0.01,"duration_seconds":10.1}\n\n',
            ],
        ),
    )


def _check_request(request: Optional[Request], version: Any = "production", task_id: str = "city-to-capital"):
    assert request is not None
    assert request.url == f"http://localhost:8000/v1/_/tasks/{task_id}/schemas/1/run"
    body = json.loads(request.content)
    assert body == {
        "task_input": {"city": "Hello"},
        "version": version,
        "stream": False,
    }
    assert request.headers["Authorization"] == "Bearer test"
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["x-workflowai-source"] == "sdk"
    assert request.headers["x-workflowai-language"] == "python"


async def test_run_task(httpx_mock: HTTPXMock) -> None:
    @workflowai.task(schema_id=1)
    async def city_to_capital(task_input: CityToCapitalTaskInput) -> CityToCapitalTaskOutput: ...

    _mock_response(httpx_mock)

    task_input = CityToCapitalTaskInput(city="Hello")
    task_output = await city_to_capital(task_input)

    assert task_output.capital == "Tokyo"

    _check_request(httpx_mock.get_request())


async def test_run_task_run(httpx_mock: HTTPXMock) -> None:
    @workflowai.task(schema_id=1)
    async def city_to_capital(task_input: CityToCapitalTaskInput) -> Run[CityToCapitalTaskOutput]: ...

    _mock_response(httpx_mock)

    task_input = CityToCapitalTaskInput(city="Hello")
    with_run = await city_to_capital(task_input)

    assert with_run.id == "123"
    assert with_run.task_output.capital == "Tokyo"

    _check_request(httpx_mock.get_request())


async def test_run_task_run_version(httpx_mock: HTTPXMock) -> None:
    @workflowai.task(schema_id=1, version="staging")
    async def city_to_capital(task_input: CityToCapitalTaskInput) -> Run[CityToCapitalTaskOutput]: ...

    _mock_response(httpx_mock)

    task_input = CityToCapitalTaskInput(city="Hello")
    with_run = await city_to_capital(task_input)

    assert with_run.id == "123"
    assert with_run.task_output.capital == "Tokyo"

    _check_request(httpx_mock.get_request(), version="staging")


async def test_stream_task_run(httpx_mock: HTTPXMock) -> None:
    @workflowai.task(schema_id=1)
    def city_to_capital(task_input: CityToCapitalTaskInput) -> AsyncIterator[CityToCapitalTaskOutput]: ...

    _mock_stream(httpx_mock)

    task_input = CityToCapitalTaskInput(city="Hello")
    chunks = [chunk async for chunk in city_to_capital(task_input)]

    assert chunks == [
        CityToCapitalTaskOutput(capital=""),
        CityToCapitalTaskOutput(capital="Tok"),
        CityToCapitalTaskOutput(capital="Tokyo"),
        CityToCapitalTaskOutput(capital="Tokyo"),
    ]


async def test_stream_task_run_custom_id(httpx_mock: HTTPXMock) -> None:
    @workflowai.task(schema_id=1, task_id="custom-id")
    def city_to_capital(task_input: CityToCapitalTaskInput) -> AsyncIterator[CityToCapitalTaskOutput]: ...

    _mock_stream(httpx_mock, task_id="custom-id")

    task_input = CityToCapitalTaskInput(city="Hello")
    chunks = [chunk async for chunk in city_to_capital(task_input)]

    assert chunks == [
        CityToCapitalTaskOutput(capital=""),
        CityToCapitalTaskOutput(capital="Tok"),
        CityToCapitalTaskOutput(capital="Tokyo"),
        CityToCapitalTaskOutput(capital="Tokyo"),
    ]
