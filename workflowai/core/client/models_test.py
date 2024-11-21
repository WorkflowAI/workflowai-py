import pytest

from tests.utils import fixture_text
from workflowai.core.client.models import RunResponse


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
