import json
from typing import Any, AsyncIterator, Optional

from httpx import Request
from pydantic import BaseModel
from pytest_httpx import HTTPXMock, IteratorStream

import workflowai
from workflowai.core.domain.run import Run


class CityToCapitalTaskInput(BaseModel):
    city: str


class CityToCapitalTaskOutput(BaseModel):
    capital: str


workflowai.init(api_key="test", url="https://run.workflowai.dev")

_REGISTER_URL = "https://api.workflowai.dev/v1/_/agents"


def _mock_register(httpx_mock: HTTPXMock, schema_id: int = 1, task_id: str = "city-to-capital", variant_id: str = "1"):
    httpx_mock.add_response(
        method="POST",
        url=_REGISTER_URL,
        json={"schema_id": schema_id, "variant_id": variant_id, "id": task_id},
    )


def _mock_response(httpx_mock: HTTPXMock, task_id: str = "city-to-capital", capital: str = "Tokyo"):
    httpx_mock.add_response(
        method="POST",
        url=f"https://run.workflowai.dev/v1/_/agents/{task_id}/schemas/1/run",
        json={"id": "123", "task_output": {"capital": capital}},
    )


def _mock_stream(httpx_mock: HTTPXMock, task_id: str = "city-to-capital"):
    httpx_mock.add_response(
        url=f"https://run.workflowai.dev/v1/_/agents/{task_id}/schemas/1/run",
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
    assert request.url == f"https://run.workflowai.dev/v1/_/agents/{task_id}/schemas/1/run"
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
    @workflowai.agent(schema_id=1)
    async def city_to_capital(task_input: CityToCapitalTaskInput) -> CityToCapitalTaskOutput: ...

    _mock_response(httpx_mock)

    task_input = CityToCapitalTaskInput(city="Hello")
    output = await city_to_capital(task_input)

    assert output.capital == "Tokyo"

    _check_request(httpx_mock.get_request())


async def test_run_task_run(httpx_mock: HTTPXMock) -> None:
    @workflowai.agent(schema_id=1)
    async def city_to_capital(task_input: CityToCapitalTaskInput) -> Run[CityToCapitalTaskOutput]: ...

    _mock_response(httpx_mock)

    task_input = CityToCapitalTaskInput(city="Hello")
    with_run = await city_to_capital(task_input)

    assert with_run.id == "123"
    assert with_run.output.capital == "Tokyo"

    _check_request(httpx_mock.get_request())


async def test_run_task_run_version(httpx_mock: HTTPXMock) -> None:
    @workflowai.agent(schema_id=1, version="staging")
    async def city_to_capital(task_input: CityToCapitalTaskInput) -> Run[CityToCapitalTaskOutput]: ...

    _mock_response(httpx_mock)

    task_input = CityToCapitalTaskInput(city="Hello")
    with_run = await city_to_capital(task_input)

    assert with_run.id == "123"
    assert with_run.output.capital == "Tokyo"

    _check_request(httpx_mock.get_request(), version="staging")


async def test_stream_task_run(httpx_mock: HTTPXMock) -> None:
    @workflowai.agent(schema_id=1)
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
    @workflowai.agent(schema_id=1, id="custom-id")
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


async def test_auto_register(httpx_mock: HTTPXMock):
    @workflowai.agent()
    async def city_to_capital(task_input: CityToCapitalTaskInput) -> CityToCapitalTaskOutput: ...

    _mock_register(httpx_mock)

    _mock_response(httpx_mock)

    res = await city_to_capital(CityToCapitalTaskInput(city="Hello"))
    assert res.capital == "Tokyo"

    _mock_response(httpx_mock, capital="Paris")
    # Run it a second time
    res = await city_to_capital(CityToCapitalTaskInput(city="Hello"), use_cache="never")
    assert res.capital == "Paris"

    req = httpx_mock.get_requests()
    assert len(req) == 3
    assert req[0].url == _REGISTER_URL

    req_body = json.loads(req[0].read())
    assert req_body == {
        "id": "city-to-capital",
        "input_schema": {
            "properties": {
                "city": {
                    "title": "City",
                    "type": "string",
                },
            },
            "required": [
                "city",
            ],
            "title": "CityToCapitalTaskInput",
            "type": "object",
        },
        "output_schema": {
            "properties": {
                "capital": {
                    "title": "Capital",
                    "type": "string",
                },
            },
            "required": [
                "capital",
            ],
            "title": "CityToCapitalTaskOutput",
            "type": "object",
        },
    }
