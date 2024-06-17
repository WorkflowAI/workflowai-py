import pytest
from pytest_httpx import HTTPXMock, IteratorStream

from tests.models.hello_task import HelloTask, HelloTaskInput, HelloTaskOutput
from tests.utils import fixtures_json
from workflowai.core.client import Client
from workflowai.core.client.client import WorkflowAIClient


@pytest.fixture(scope="function")
def client():
    return WorkflowAIClient(endpoint="http://localhost:8000", api_key="test")


class TestRegister:
    async def test_success(self, httpx_mock: HTTPXMock, client: WorkflowAIClient):
        httpx_mock.add_response(
            json={
                "task_id": "123",
                "task_schema_id": 1,
                "created_at": "2022-01-01T00:00:00Z",
                "name": "Hello",
                "input_schema": {"version": "1", "json_schema": {}},
                "output_schema": {"version": "1", "json_schema": {}},
            }
        )
        task = HelloTask()
        assert task.id == "", "sanity"
        assert task.schema_id == 0, "sanity"

        await client.register(task)

        assert task.id == "123"
        assert task.schema_id == 1


class TestRun:
    async def test_success(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))
        task = HelloTask(id="123", schema_id=1)

        task_run = await client.run(task, task_input=HelloTaskInput(name="Alice"))

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

    async def test_stream(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(
            stream=IteratorStream(
                [
                    b'data: {"message": ""}',
                    b'data: {"message": "hel"}',
                    b'data: {"message": "hello"}',
                ]
            )
        )
        task = HelloTask(id="123", schema_id=1)

        streamed = await client.run(
            task, task_input=HelloTaskInput(name="Alice"), stream=True
        )
        chunks = [chunk async for chunk in streamed]

        assert chunks == [
            HelloTaskOutput(message=""),
            HelloTaskOutput(message="hel"),
            HelloTaskOutput(message="hello"),
        ]
