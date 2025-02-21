from unittest.mock import Mock, patch

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
        id="run-id",
        agent_id="agent-id",
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


# Test that format_output correctly formats:
# 1. The output as a JSON object
# 2. The cost with $ prefix and correct precision
# 3. The latency with 2 decimal places and 's' suffix
# 4. The run URL
@patch("workflowai.env.WORKFLOWAI_APP_URL", "https://workflowai.hello")
def test_format_output_full():
    run = Run[_TestOutput](
        id="run-id",
        agent_id="agent-id",
        schema_id=1,
        output=_TestOutput(message="hello"),
        duration_seconds=1.23,
        cost_usd=0.001,
    )

    expected = """\nOutput:
==================================================
{
  "message": "hello"
}
==================================================
Cost: $ 0.00100
Latency: 1.23s
URL: https://workflowai.hello/_/agents/agent-id/runs/run-id"""

    assert run.format_output() == expected


@patch("workflowai.env.WORKFLOWAI_APP_URL", "https://workflowai.hello")
def test_format_output_very_low_cost():
    run = Run[_TestOutput](
        id="run-id",
        agent_id="agent-id",
        schema_id=1,
        output=_TestOutput(message="hello"),
        duration_seconds=1.23,
        cost_usd=4.97625e-05,
    )

    expected = """\nOutput:
==================================================
{
  "message": "hello"
}
==================================================
Cost: $ 0.00005
Latency: 1.23s
URL: https://workflowai.hello/_/agents/agent-id/runs/run-id"""

    assert run.format_output() == expected


# Test that format_output works correctly when cost and latency are not provided:
# 1. The output is still formatted as a JSON object
# 2. No cost or latency lines are included in the output
# 3. The run URL is still included
@patch("workflowai.env.WORKFLOWAI_APP_URL", "https://workflowai.hello")
def test_format_output_no_cost_latency():
    run = Run[_TestOutput](
        id="run-id",
        agent_id="agent-id",
        schema_id=1,
        output=_TestOutput(message="hello"),
    )

    expected = """\nOutput:
==================================================
{
  "message": "hello"
}
==================================================
URL: https://workflowai.hello/_/agents/agent-id/runs/run-id"""

    assert run.format_output() == expected


class TestRunURL:
    @patch("workflowai.env.WORKFLOWAI_APP_URL", "https://workflowai.hello")
    def test_run_url(self, run1: Run[_TestOutput]):
        assert run1.run_url == "https://workflowai.hello/_/agents/agent-id/runs/run-id"
