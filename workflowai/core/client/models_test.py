import pytest

from tests.utils import fixture_text
from workflowai.core.client.models import TaskRunResponse


@pytest.mark.parametrize(
    "fixture",
    [
        "task_run.json",
        "task_run_float_usage.json",
    ],
)
def test_task_run_response(fixture: str):
    txt = fixture_text(fixture)
    task_run = TaskRunResponse.model_validate_json(txt)
    assert task_run
