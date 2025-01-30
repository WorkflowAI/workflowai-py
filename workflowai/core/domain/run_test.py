from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from workflowai.core.domain.run import Run
from workflowai.core.domain.version import Version
from workflowai.core.domain.version_properties import VersionProperties


class _TestOutput(BaseModel):
    message: str


@pytest.fixture
def run1() -> Run[_TestOutput]:
    return Run[_TestOutput](
        id="test-id",
        agent_id="agent-1",
        schema_id=1,
        output=_TestOutput(message="test output"),
        duration_seconds=1.0,
        cost_usd=0.1,
        version=Version(properties=VersionProperties()),
        metadata={"test": "data"},
        tool_calls=[],
        tool_call_requests=[],
    )


@pytest.fixture
def run2(run1: Run[_TestOutput]) -> Run[_TestOutput]:
    return run1.model_copy(deep=True)


class TestRunEquality:
    def test_identical(self, run1: Run[_TestOutput], run2: Run[_TestOutput]):
        assert run1 == run2

    def test_different_output(self, run1: Run[_TestOutput], run2: Run[_TestOutput]):
        run2.output.message = "different output"
        assert run1 != run2

    def test_different_agents(self, run1: Run[_TestOutput], run2: Run[_TestOutput]):
        run2._agent = Mock()  # pyright: ignore [reportPrivateUsage]
        assert run1._agent != run2._agent, "sanity check"  # pyright: ignore [reportPrivateUsage]
        assert run1 == run2
