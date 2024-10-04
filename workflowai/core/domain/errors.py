from json import JSONDecodeError
from typing import Any, Literal, Optional, Union

from httpx import Response
from pydantic import BaseModel

ProviderErrorCode = Literal[
    # Max number of tokens were exceeded in the prompt
    "max_tokens_exceeded",
    # The model failed to generate a response
    "failed_generation",
    # The model generated a response but it was not valid
    "invalid_generation",
    # The model returned an error that we currently do not handle
    # The returned status code will match the provider status code and the entire
    # provider response will be provided the error details.
    #
    # This error is intended as a fallback since we do not control what the providers
    # return. We track this error on our end and the error should eventually
    # be assigned a different status code
    "unknown_provider_error",
    # The provider returned a rate limit error
    "rate_limit",
    # The provider returned a server overloaded error
    "server_overloaded",
    # The requested provider does not support the model
    "invalid_provider_config",
    # The provider returned a 500
    "provider_internal_error",
    # The provider returned a 502 or 503
    "provider_unavailable",
    # The request timed out
    "read_timeout",
    # The requested model does not support the requested generation mode
    # (e-g a model that does not support images generation was sent an image)
    "model_does_not_support_mode",
]

ErrorCode = Union[
    ProviderErrorCode,
    Literal[
        # The object was not found
        "object_not_found",
        # There are no configured providers supporting the requested model
        # This error will never happen when using WorkflowAI keys
        "no_provider_supporting_model",
        # The requested provider does not support the model
        "provider_does_not_support_model",
        # Run properties are invalid, for example the model does not exist
        "invalid_run_properties",
        # An internal error occurred
        "internal_error",
        # The request was invalid
        "bad_request",
        "invalid_file",
    ],
    str,  # Using as a fallback to avoid validation error if an error code is added to the API
]


class BaseError(BaseModel):
    details: Optional[dict[str, Any]] = None
    message: str
    status_code: Optional[int] = None
    code: Optional[ErrorCode] = None


class ErrorResponse(BaseModel):
    error: BaseError
    task_run_id: Optional[str] = None


class WorkflowAIError(Exception):
    def __init__(self, response: Optional[Response], error: BaseError, task_run_id: Optional[str] = None):
        self.error = error
        self.task_run_id = task_run_id
        self.response = response

    def __str__(self):
        return f"WorkflowAIError : [{self.error.code}] ({self.error.status_code}): [{self.error.message}]"

    @classmethod
    def from_response(cls, response: Response):
        try:
            response_json = response.json()
            r_error = response_json.get("error", {})
            error_message = response_json.get("detail", {}) or r_error.get("message", "Unknown Error")
            details = r_error.get("details", {})
            error_code = r_error.get("code", "unknown_error")
            status_code = response.status_code
            task_run_id = r_error.get("task_run_id", None)
        except JSONDecodeError:
            error_message = "Unknown error"
            details = {"raw": response.content.decode()}
            error_code = "unknown_error"
            status_code = response.status_code
            task_run_id = None

        return cls(
            response=response,
            error=BaseError(
                message=error_message,
                details=details,
                status_code=status_code,
                code=error_code,
            ),
            task_run_id=task_run_id,
        )
