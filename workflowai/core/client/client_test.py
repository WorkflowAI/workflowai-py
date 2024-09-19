import json

import pytest
from pytest_httpx import HTTPXMock, IteratorStream

from tests.models.hello_task import HelloTask, HelloTaskInput, HelloTaskOutput
from tests.utils import fixtures_json
from workflowai.core.client import Client
from workflowai.core.client.client import WorkflowAIClient
from workflowai.core.domain.llm_completion import LLMCompletion
from workflowai.core.domain.task_example import TaskExample
from workflowai.core.domain.task_run import TaskRun
from workflowai.core.domain.task_version import TaskVersion


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

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/tasks/123/schemas/1/run"

        body = json.loads(reqs[0].content)
        assert body == {
            "task_input": {"name": "Alice"},
            "group": {"properties": {}},
            "stream": False,
            "use_cache": "when_available",
        }

    async def test_stream(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(
            stream=IteratorStream(
                [
                    b'data: {"run_id":"1","task_output":{"message":""}}',
                    b'data: {"run_id":"1","task_output":{"message":"hel"}}',
                    b'data: {"run_id":"1","task_output":{"message":"hello"}}',
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

    async def test_run_with_env(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))
        task = HelloTask(id="123", schema_id=1)

        await client.run(
            task,
            task_input=HelloTaskInput(name="Alice"),
            environment="dev",
        )

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/tasks/123/schemas/1/run"

        body = json.loads(reqs[0].content)
        assert body == {
            "task_input": {"name": "Alice"},
            "group": {"alias": "environment=dev"},
            "stream": False,
            "use_cache": "when_available",
        }

    async def test_run_retries_on_too_many_requests(self, httpx_mock: HTTPXMock, client: Client):
        task = HelloTask(id="123", schema_id=1)

        httpx_mock.add_response(status_code=429)
        httpx_mock.add_response(json=fixtures_json("task_run.json"))

        task_run = await client.run(task, task_input=HelloTaskInput(name="Alice"), max_retry_count=5)

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 2  
        assert reqs[0].url == "http://localhost:8000/tasks/123/schemas/1/run"
        assert reqs[1].url == "http://localhost:8000/tasks/123/schemas/1/run"

class TestImportRun:
    async def test_success(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(json=fixtures_json("task_run.json"))
        task = HelloTask(id="123", schema_id=1)

        run = TaskRun(
            task=task,
            task_input=HelloTaskInput(name="Alice"),
            task_output=HelloTaskOutput(message="hello"),
            version=TaskVersion(iteration=1),
            llm_completions=[
                LLMCompletion(messages=[{"content": "hello"}], response="world"),
            ],
        )

        imported = await client.import_run(run)
        assert imported.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/tasks/123/schemas/1/runs"

        body = json.loads(reqs[0].content)
        assert body == {
            "id": run.id,
            "task_input": {"name": "Alice"},
            "task_output": {"message": "hello"},
            "group": {"iteration": 1},
            "llm_completions": [
                {
                    "messages": [
                        {
                            "content": "hello",
                        },
                    ],
                    "response": "world",
                },
            ],
        }


class TestImportExample:
    async def test_success(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(json=fixtures_json("task_example.json"))
        task = HelloTask(id="123", schema_id=1)

        example = TaskExample(
            task=task,
            task_input=HelloTaskInput(name="Alice"),
            task_output=HelloTaskOutput(message="hello"),
        )

        imported = await client.import_example(example)
        assert imported.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/tasks/123/schemas/1/examples"

        body = json.loads(reqs[0].content)
        assert body == {
            "task_input": {"name": "Alice"},
            "task_output": {"message": "hello"},
        }

class TestDeployVersion:
    async def test_success(self, httpx_mock: HTTPXMock, client: Client):
        httpx_mock.add_response(json=fixtures_json("task_version.json"))
        task = HelloTask(id="123", schema_id=1)

        version = await client.deploy_version(task, iteration=1, environment="dev")
        assert version.iteration == 1

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 1
        assert reqs[0].url == "http://localhost:8000/tasks/123/schemas/1/groups/1"

        body = json.loads(reqs[0].content)
        assert body == {
            "add_alias": "environment=dev",
        }
