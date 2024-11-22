from typing import Optional

import pytest
from pydantic import BaseModel, ValidationError

from tests.utils import fixture_text
from workflowai.core.client.models import RunResponse, RunStreamChunk
from workflowai.core.domain.task import Task
from workflowai.core.domain.task_run import Run, RunChunk


@pytest.mark.parametrize(
    "fixture",
    [
        "task_run.json",
    ],
)
def test_task_run_response(fixture: str):
    txt = fixture_text(fixture)
    task_run = RunResponse.model_validate_json(txt)
    assert task_run


class _TaskOutput(BaseModel):
    a: int
    b: str


class _TaskOutputOpt(BaseModel):
    a: Optional[int] = None
    b: Optional[str] = None


class _Task(Task[_TaskOutput, _TaskOutput]):
    id: str = "test-task"
    schema_id: int = 1
    input_class: type[_TaskOutput] = _TaskOutput
    output_class: type[_TaskOutput] = _TaskOutput


class _TaskOpt(Task[_TaskOutputOpt, _TaskOutputOpt]):
    id: str = "test-task"
    schema_id: int = 1
    input_class: type[_TaskOutputOpt] = _TaskOutputOpt
    output_class: type[_TaskOutputOpt] = _TaskOutputOpt


class TestRunStreamChunkToDomain:
    def test_no_version_not_optional(self):
        # Check that partial model is ok
        chunk = RunStreamChunk.model_validate_json('{"id": "1", "task_output": {"a": 1}}')
        assert chunk.task_output == {"a": 1}

        with pytest.raises(ValidationError):  # sanity
            _TaskOutput.model_validate({"a": 1})

        parsed = chunk.to_domain(_Task())
        assert isinstance(parsed, RunChunk)
        assert parsed.task_output.a == 1
        # b is not defined
        with pytest.raises(AttributeError):
            assert parsed.task_output.b

    def test_no_version_optional(self):
        chunk = RunStreamChunk.model_validate_json('{"id": "1", "task_output": {"a": 1}}')
        assert chunk

        parsed = chunk.to_domain(_TaskOpt())
        assert isinstance(parsed, RunChunk)
        assert parsed.task_output.a == 1
        assert parsed.task_output.b is None

    def test_with_version(self):
        chunk = RunStreamChunk.model_validate_json(
            '{"id": "1", "task_output": {"a": 1, "b": "test"}, "cost_usd": 0.1, "duration_seconds": 1, "version": {"properties": {"a": 1, "b": "test"}}}',  # noqa: E501
        )
        assert chunk

        parsed = chunk.to_domain(_Task())
        assert isinstance(parsed, Run)
        assert parsed.task_output.a == 1
        assert parsed.task_output.b == "test"

        assert parsed.cost_usd == 0.1
        assert parsed.duration_seconds == 1

    def test_with_version_validation_fails(self):
        chunk = RunStreamChunk.model_validate_json(
            '{"id": "1", "task_output": {"a": 1}, "version": {"properties": {"a": 1, "b": "test"}}}',
        )
        with pytest.raises(ValidationError):
            chunk.to_domain(_Task())
