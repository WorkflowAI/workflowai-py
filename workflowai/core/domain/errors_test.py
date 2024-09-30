
from unittest.mock import Mock

from workflowai.core.domain.errors import WorkflowAIError


def test_workflow_ai_error_404():
    response = Mock()
    response.status_code = 404
    response.json = Mock()
    response.json.return_value = {"error": {"message": "None", "status_code": 404, "code": "object_not_found"}}

    error = WorkflowAIError.from_response(response)
    assert error.error.message == "None"
    assert error.error.status_code == 404
    assert error.error.code == "object_not_found"
