import importlib.metadata
import json

import pytest
from pytest_httpx import HTTPXMock, IteratorStream

from tests.models.hello_task import HelloTask, HelloTaskInput, HelloTaskNotOptional, HelloTaskOutput
from tests.utils import fixtures_json
from workflowai.core.client import Client
from workflowai.core.client.client import WorkflowAIClient
from workflowai.core.domain.task_run import Run


@pytest.fixture
def client():
    return WorkflowAIClient(endpoint="http://localhost:8000", api_key="test")


class TestRun:
    async def test_success(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))
        task = HelloTask(id="123", schema_id=1)

        task_run = await client.run(task, task_input=HelloTaskInput(name="Alice"))

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/v1/_/tasks/123/schemas/1/run"

        body = json.loads(reqs[0].content)
        assert body == {
            "task_input": {"name": "Alice"},
            "version": "production",
            "stream": False,
            "use_cache": "when_available",
        }

    async def test_stream(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(
            stream=IteratorStream(
                [
                    b'data: {"id":"1","task_output":{"message":""}}\n\n',
                    b'data: {"id":"1","task_output":{"message":"hel"}}\n\ndata: {"id":"1","task_output":{"message":"hello"}}\n\n',  # noqa: E501
                    b'data: {"id":"1","task_output":{"message":"hello"},"version":{"properties":{"model":"gpt-4o","temperature":0.5}},"cost_usd":0.01,"duration_seconds":10.1}\n\n',  # noqa: E501
                ],
            ),
        )
        task = HelloTask(id="123", schema_id=1)

        streamed = await client.run(
            task,
            task_input=HelloTaskInput(name="Alice"),
            stream=True,
        )
        chunks = [chunk async for chunk in streamed]

        outputs = [chunk.task_output for chunk in chunks]
        assert outputs == [
            HelloTaskOutput(message=""),
            HelloTaskOutput(message="hel"),
            HelloTaskOutput(message="hello"),
            HelloTaskOutput(message="hello"),
        ]
        last_message = chunks[-1]
        assert isinstance(last_message, Run)
        assert last_message.version.properties.model == "gpt-4o"
        assert last_message.version.properties.temperature == 0.5
        assert last_message.cost_usd == 0.01
        assert last_message.duration_seconds == 10.1

    async def test_stream_not_optional(self, httpx_mock: HTTPXMock, client: Client):
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
        task = HelloTaskNotOptional(id="123", schema_id=1)

        streamed = await client.run(
            task,
            task_input=HelloTaskInput(name="Alice"),
            stream=True,
        )
        chunks = [chunk async for chunk in streamed]

        messages = [chunk.task_output.message for chunk in chunks]
        assert messages == ["", "hel", "hello", "hello"]

        for chunk in chunks[:-1]:
            with pytest.raises(AttributeError):
                # Since the field is not optional, it will raise an attribute error
                assert chunk.task_output.another_field
        assert chunks[-1].task_output.another_field == "test"

        last_message = chunks[-1]
        assert isinstance(last_message, Run)
        assert last_message.version.properties.model == "gpt-4o"
        assert last_message.version.properties.temperature == 0.5
        assert last_message.cost_usd == 0.01
        assert last_message.duration_seconds == 10.1

    async def test_run_with_env(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))
        task = HelloTask(id="123", schema_id=1)

        await client.run(
            task,
            task_input=HelloTaskInput(name="Alice"),
            version="dev",
        )

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/v1/_/tasks/123/schemas/1/run"

        body = json.loads(reqs[0].content)
        assert body == {
            "task_input": {"name": "Alice"},
            "version": "dev",
            "stream": False,
            "use_cache": "when_available",
        }

    async def test_success_with_headers(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))
        task = HelloTask(id="123", schema_id=1)

        task_run = await client.run(task, task_input=HelloTaskInput(name="Alice"))

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/v1/_/tasks/123/schemas/1/run"
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
            "use_cache": "when_available",
        }
        # Check for additional headers
        for key, value in headers.items():
            assert reqs[0].headers[key] == value

    async def test_run_retries_on_too_many_requests(self, httpx_mock: HTTPXMock, client: Client):
        task = HelloTask(id="123", schema_id=1)

        httpx_mock.add_response(headers={"Retry-After": "0.01"}, status_code=429)
        httpx_mock.add_response(json=fixtures_json("task_run.json"))

        task_run = await client.run(task, task_input=HelloTaskInput(name="Alice"), max_retry_count=5)

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 2
        assert reqs[0].url == "http://localhost:8000/v1/_/tasks/123/schemas/1/run"
        assert reqs[1].url == "http://localhost:8000/v1/_/tasks/123/schemas/1/run"
