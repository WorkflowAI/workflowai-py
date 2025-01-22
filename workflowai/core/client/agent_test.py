import importlib.metadata
import json

import httpx
import pytest
from pytest_httpx import HTTPXMock, IteratorStream

from tests.models.hello_task import (
    HelloTaskInput,
    HelloTaskOutput,
    HelloTaskOutputNotOptional,
)
from tests.utils import fixtures_json
from workflowai.core.client._api import APIClient
from workflowai.core.client.agent import Agent
from workflowai.core.client.client import (
    WorkflowAI,
)
from workflowai.core.domain.errors import WorkflowAIError
from workflowai.core.domain.run import Run


@pytest.fixture
def api_client():
    return WorkflowAI(endpoint="http://localhost:8000", api_key="test").api


@pytest.fixture
def agent(api_client: APIClient):
    return Agent(agent_id="123", schema_id=1, input_cls=HelloTaskInput, output_cls=HelloTaskOutput, api=api_client)


@pytest.fixture
def agent_not_optional(api_client: APIClient):
    return Agent(
        agent_id="123",
        schema_id=1,
        input_cls=HelloTaskInput,
        output_cls=HelloTaskOutputNotOptional,
        api=api_client,
    )


@pytest.fixture
def agent_no_schema(api_client: APIClient):
    return Agent(
        agent_id="123",
        input_cls=HelloTaskInput,
        output_cls=HelloTaskOutput,
        api=api_client,
    )


class TestRun:
    async def test_success(self, httpx_mock: HTTPXMock, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))

        task_run = await agent.run(task_input=HelloTaskInput(name="Alice"))

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"
        assert task_run.task_id == "123"
        assert task_run.task_schema_id == 1

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/v1/_/agents/123/schemas/1/run"

        body = json.loads(reqs[0].content)
        assert body == {
            "task_input": {"name": "Alice"},
            "version": "production",
            "stream": False,
        }

    async def test_stream(self, httpx_mock: HTTPXMock, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        httpx_mock.add_response(
            stream=IteratorStream(
                [
                    b'data: {"id":"1","task_output":{"message":""}}\n\n',
                    b'data: {"id":"1","task_output":{"message":"hel"}}\n\ndata: {"id":"1","task_output":{"message":"hello"}}\n\n',  # noqa: E501
                    b'data: {"id":"1","task_output":{"message":"hello"},"version":{"properties":{"model":"gpt-4o","temperature":0.5}},"cost_usd":0.01,"duration_seconds":10.1}\n\n',  # noqa: E501
                ],
            ),
        )

        chunks = [chunk async for chunk in agent.stream(task_input=HelloTaskInput(name="Alice"))]

        outputs = [chunk.task_output for chunk in chunks]
        assert outputs == [
            HelloTaskOutput(message=""),
            HelloTaskOutput(message="hel"),
            HelloTaskOutput(message="hello"),
            HelloTaskOutput(message="hello"),
        ]
        last_message = chunks[-1]
        assert isinstance(last_message, Run)
        assert last_message.version
        assert last_message.version.properties.model == "gpt-4o"
        assert last_message.version.properties.temperature == 0.5
        assert last_message.cost_usd == 0.01
        assert last_message.duration_seconds == 10.1

    async def test_stream_not_optional(
        self,
        httpx_mock: HTTPXMock,
        agent_not_optional: Agent[HelloTaskInput, HelloTaskOutputNotOptional],
    ):
        # Checking that streaming works even with non optional fields
        # The first two chunks are missing a required key but the last one has it
        httpx_mock.add_response(
            stream=IteratorStream(
                [
                    b'data: {"id":"1","task_output":{"message":""}}\n\n',
                    b'data: {"id":"1","task_output":{"message":"hel"}}\n\ndata: {"id":"1","task_output":{"message":"hello"}}\n\n',  # noqa: E501
                    b'data: {"id":"1","task_output":{"message":"hello", "another_field": "test"},"version":{"properties":{"model":"gpt-4o","temperature":0.5}},"cost_usd":0.01,"duration_seconds":10.1}\n\n',  # noqa: E501
                ],
            ),
        )

        chunks = [chunk async for chunk in agent_not_optional.stream(task_input=HelloTaskInput(name="Alice"))]

        messages = [chunk.task_output.message for chunk in chunks]
        assert messages == ["", "hel", "hello", "hello"]

        for chunk in chunks[:-1]:
            with pytest.raises(AttributeError):
                # Since the field is not optional, it will raise an attribute error
                assert chunk.task_output.another_field
        assert chunks[-1].task_output.another_field == "test"

        last_message = chunks[-1]
        assert isinstance(last_message, Run)
        assert last_message.version
        assert last_message.version.properties.model == "gpt-4o"
        assert last_message.version.properties.temperature == 0.5
        assert last_message.cost_usd == 0.01
        assert last_message.duration_seconds == 10.1

    async def test_run_with_env(self, httpx_mock: HTTPXMock, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))

        await agent.run(
            task_input=HelloTaskInput(name="Alice"),
            version="dev",
        )

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/v1/_/agents/123/schemas/1/run"

        body = json.loads(reqs[0].content)
        assert body == {
            "task_input": {"name": "Alice"},
            "version": "dev",
            "stream": False,
        }

    async def test_success_with_headers(self, httpx_mock: HTTPXMock, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))

        task_run = await agent.run(task_input=HelloTaskInput(name="Alice"))

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/v1/_/agents/123/schemas/1/run"
        headers = {
            "x-workflowai-source": "sdk",
            "x-workflowai-language": "python",
            "x-workflowai-version": importlib.metadata.version("workflowai"),
        }

        body = json.loads(reqs[0].content)
        assert body == {
            "task_input": {"name": "Alice"},
            "version": "production",
            "stream": False,
        }
        # Check for additional headers
        for key, value in headers.items():
            assert reqs[0].headers[key] == value

    async def test_run_retries_on_too_many_requests(
        self,
        httpx_mock: HTTPXMock,
        agent: Agent[HelloTaskInput, HelloTaskOutput],
    ):
        httpx_mock.add_response(
            url="http://localhost:8000/v1/_/agents/123/schemas/1/run",
            headers={"Retry-After": "0.01"},
            status_code=429,
        )
        httpx_mock.add_response(
            url="http://localhost:8000/v1/_/agents/123/schemas/1/run",
            json=fixtures_json("task_run.json"),
        )

        task_run = await agent.run(task_input=HelloTaskInput(name="Alice"), max_retry_count=5)

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 2

    async def test_run_retries_on_connection_error(
        self,
        httpx_mock: HTTPXMock,
        agent: Agent[HelloTaskInput, HelloTaskOutput],
    ):
        httpx_mock.add_exception(httpx.ConnectError("arg"))
        httpx_mock.add_exception(httpx.ConnectError("arg"))
        httpx_mock.add_response(json=fixtures_json("task_run.json"))

        task_run = await agent.run(task_input=HelloTaskInput(name="Alice"), max_retry_count=5)
        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

    async def test_max_retries(self, httpx_mock: HTTPXMock, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        httpx_mock.add_exception(httpx.ConnectError("arg"), is_reusable=True)
        httpx_mock.add_exception(httpx.ConnectError("arg"), is_reusable=True)

        with pytest.raises(WorkflowAIError):
            await agent.run(task_input=HelloTaskInput(name="Alice"), max_retry_count=5)

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 5

    async def test_auto_register(self, httpx_mock: HTTPXMock, agent_no_schema: Agent[HelloTaskInput, HelloTaskOutput]):
        httpx_mock.add_response(
            url="http://localhost:8000/v1/_/agents",
            json={
                "id": "123",
                "schema_id": 2,
            },
        )
        run_response = fixtures_json("task_run.json")
        httpx_mock.add_response(
            url="http://localhost:8000/v1/_/agents/123/schemas/2/run",
            json=run_response,
        )

        out = await agent_no_schema.run(task_input=HelloTaskInput(name="Alice"))
        assert out.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        run_response["id"] = "8f635b73-f403-47ee-bff9-18320616c6cc"
        # Try and run again
        httpx_mock.add_response(
            url="http://localhost:8000/v1/_/agents/123/schemas/2/run",
            json=run_response,
        )
        out2 = await agent_no_schema.run(task_input=HelloTaskInput(name="Alice"))
        assert out2.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 3
        assert reqs[0].url == "http://localhost:8000/v1/_/agents"
        assert reqs[1].url == "http://localhost:8000/v1/_/agents/123/schemas/2/run"
        assert reqs[2].url == "http://localhost:8000/v1/_/agents/123/schemas/2/run"
