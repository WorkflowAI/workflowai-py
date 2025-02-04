from typing import Any, Optional

import pytest

import workflowai
from tests.integration.conftest import CityToCapitalTaskInput, CityToCapitalTaskOutput, IntTestClient
from workflowai.core.domain.errors import InvalidGenerationError
from workflowai.core.domain.run import Run


class TestRecoverableError:
    def _mock_agent_run_failed(self, test_client: IntTestClient, output: Optional[dict[str, Any]] = None):
        # The agent run
        test_client.mock_response(
            status_code=424,
            json={
                "id": "123",
                "task_output": output or {"capital": "Tokyo"},
                "error": {
                    "code": "agent_run_failed",
                    "message": "Test error message",
                },
            },
        )

    async def test_output_only(self, test_client: IntTestClient):
        @workflowai.agent(schema_id=1)
        async def city_to_capital(task_input: CityToCapitalTaskInput) -> CityToCapitalTaskOutput: ...

        self._mock_agent_run_failed(test_client)

        with pytest.raises(InvalidGenerationError) as e:
            await city_to_capital(CityToCapitalTaskInput(city="Hello"))

        assert e.value.run_id == "123"
        assert e.value.partial_output == {"capital": "Tokyo"}

    async def test_recover(self, test_client: IntTestClient):
        # When the return is a full run object we try and recover the error using a partial output

        @workflowai.agent(schema_id=1)
        async def city_to_capital(task_input: CityToCapitalTaskInput) -> Run[CityToCapitalTaskOutput]: ...

        self._mock_agent_run_failed(test_client)

        run = await city_to_capital(CityToCapitalTaskInput(city="Hello"))
        assert run.id == "123"
        assert run.output.capital == "Tokyo"

        assert run.error is not None
        assert run.error.code == "agent_run_failed"

    async def test_unrecoverable_error(self, test_client: IntTestClient):
        @workflowai.agent(schema_id=1)
        async def city_to_capital(task_input: CityToCapitalTaskInput) -> Run[CityToCapitalTaskOutput]: ...

        # Mocking with an invalid output, CityToCapitalTaskOutput requires the capital field
        self._mock_agent_run_failed(test_client, {"capitale": "Tokyo"})

        with pytest.raises(InvalidGenerationError):
            await city_to_capital(CityToCapitalTaskInput(city="Hello"))
