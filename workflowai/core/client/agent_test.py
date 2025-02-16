import importlib.metadata
import json

import httpx
import pytest
from pydantic import BaseModel, Field  # pyright: ignore [reportUnknownVariableType]
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
from workflowai.core.domain.version_properties import VersionProperties


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

        task_run = await agent.run(HelloTaskInput(name="Alice"))

        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"
        assert task_run.agent_id == "123"
        assert task_run.schema_id == 1

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

        chunks = [chunk async for chunk in agent.stream(HelloTaskInput(name="Alice"))]

        outputs = [chunk.output for chunk in chunks]
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

        chunks = [chunk async for chunk in agent_not_optional.stream(HelloTaskInput(name="Alice"))]

        messages = [chunk.output.message for chunk in chunks]
        assert messages == ["", "hel", "hello", "hello"]

        for chunk in chunks[:-1]:
            with pytest.raises(AttributeError):
                # Since the field is not optional, it will raise an attribute error
                assert chunk.output.another_field
        assert chunks[-1].output.another_field == "test"

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
            HelloTaskInput(name="Alice"),
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

        task_run = await agent.run(HelloTaskInput(name="Alice"))

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

        task_run = await agent.run(HelloTaskInput(name="Alice"), max_retry_count=5)

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

        task_run = await agent.run(HelloTaskInput(name="Alice"), max_retry_count=5)
        assert task_run.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

    async def test_max_retries(self, httpx_mock: HTTPXMock, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        httpx_mock.add_exception(httpx.ConnectError("arg"), is_reusable=True)
        httpx_mock.add_exception(httpx.ConnectError("arg"), is_reusable=True)

        with pytest.raises(WorkflowAIError):
            await agent.run(HelloTaskInput(name="Alice"), max_retry_count=5)

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

        out = await agent_no_schema.run(HelloTaskInput(name="Alice"))
        assert out.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        run_response["id"] = "8f635b73-f403-47ee-bff9-18320616c6cc"
        # Try and run again
        httpx_mock.add_response(
            url="http://localhost:8000/v1/_/agents/123/schemas/2/run",
            json=run_response,
        )
        out2 = await agent_no_schema.run(HelloTaskInput(name="Alice"))
        assert out2.id == "8f635b73-f403-47ee-bff9-18320616c6cc"

        reqs = httpx_mock.get_requests()
        assert len(reqs) == 3
        assert reqs[0].url == "http://localhost:8000/v1/_/agents"
        assert reqs[1].url == "http://localhost:8000/v1/_/agents/123/schemas/2/run"
        assert reqs[2].url == "http://localhost:8000/v1/_/agents/123/schemas/2/run"

        register_body = json.loads(reqs[0].content)
        assert register_body["input_schema"] == {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"],
        }
        assert register_body["output_schema"] == {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
            "required": ["message"],
        }

    async def test_with_alias(self, httpx_mock: HTTPXMock, api_client: APIClient):
        class AliasInput(BaseModel):
            name: str = Field(alias="name_alias")
            aliased_ser: str = Field(serialization_alias="aliased_ser_alias")
            aliased_val: str = Field(validation_alias="aliased_val_alias")

        class AliasOutput(BaseModel):
            message: str = Field(alias="message_alias")
            aliased_ser: str = Field(serialization_alias="aliased_ser_alias")
            aliased_val: str = Field(validation_alias="aliased_val_alias")

        agent = Agent(agent_id="123", input_cls=AliasInput, output_cls=AliasOutput, api=api_client)

        httpx_mock.add_response(url="http://localhost:8000/v1/_/agents", json={"id": "123", "schema_id": 2})

        httpx_mock.add_response(
            url="http://localhost:8000/v1/_/agents/123/schemas/2/run",
            json={
                "id": "1",
                # task output should be compatible with the output schema below
                "task_output": {
                    "message_alias": "1",
                    "aliased_ser": "2",
                    "aliased_val_alias": "3",
                },
            },
        )

        out2 = await agent.run(
            # Using model validate instead of constructing directly, since pyright does not
            # Understand asymmetric aliases
            AliasInput.model_validate({"name_alias": "1", "aliased_ser": "2", "aliased_val_alias": "3"}),
        )
        assert out2.output.message == "1"
        assert out2.output.aliased_ser == "2"
        assert out2.output.aliased_val == "3"

        register_req = httpx_mock.get_request(url="http://localhost:8000/v1/_/agents")
        assert register_req
        register_body = json.loads(register_req.content)
        assert register_body["input_schema"] == {
            "type": "object",
            "properties": {
                "name_alias": {"type": "string"},
                "aliased_ser_alias": {"type": "string"},
                "aliased_val": {"type": "string"},
            },
            "required": ["name_alias", "aliased_ser_alias", "aliased_val"],
        }
        assert register_body["output_schema"] == {
            "type": "object",
            "properties": {
                "message_alias": {"type": "string"},
                "aliased_ser": {"type": "string"},
                "aliased_val_alias": {"type": "string"},
            },
            "required": ["message_alias", "aliased_ser", "aliased_val_alias"],
        }

        run_req = httpx_mock.get_request(url="http://localhost:8000/v1/_/agents/123/schemas/2/run")
        assert run_req
        # Task input should be compatible with the input schema
        assert json.loads(run_req.content)["task_input"] == {
            "name_alias": "1",
            "aliased_ser_alias": "2",
            "aliased_val": "3",
        }


class TestSanitizeVersion:
    def test_string_version(self, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        assert agent._sanitize_version({"version": "production"}) == "production"  # pyright: ignore [reportPrivateUsage]

    def test_default_version(self, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        assert agent._sanitize_version({}) == "production"  # pyright: ignore [reportPrivateUsage]

    def test_version_properties(self, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        assert agent._sanitize_version({"version": VersionProperties(temperature=0.7)}) == {  # pyright: ignore [reportPrivateUsage]
            "temperature": 0.7,
            "model": "gemini-1.5-pro-latest",
        }

    def test_version_properties_with_model(self, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        # When the default version is used and we pass the model, the model has priority
        assert agent.version == "production", "sanity"
        assert agent._sanitize_version({"model": "gemini-1.5-pro-latest"}) == {  # pyright: ignore [reportPrivateUsage]
            "model": "gemini-1.5-pro-latest",
        }

    def test_version_with_models_and_version(self, agent: Agent[HelloTaskInput, HelloTaskOutput]):
        # If version is explcitly provided then it takes priority and we log a warning
        assert agent._sanitize_version({"version": "staging", "model": "gemini-1.5-pro-latest"}) == "staging"  # pyright: ignore [reportPrivateUsage]
