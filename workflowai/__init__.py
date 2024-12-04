import os
from typing import Optional

from workflowai.core.client import Client as Client
from workflowai.core.client._client import DEFAULT_VERSION_REFERENCE
from workflowai.core.client._client import WorkflowAIClient as WorkflowAIClient
from workflowai.core.client._types import TaskDecorator
from workflowai.core.domain.cache_usage import CacheUsage as CacheUsage
from workflowai.core.domain.errors import WorkflowAIError as WorkflowAIError
from workflowai.core.domain.task import Task as Task
from workflowai.core.domain.task_run import Run as Run
from workflowai.core.domain.task_version import TaskVersion as TaskVersion
from workflowai.core.domain.task_version_reference import (
    VersionReference as VersionReference,
)

# By default the shared client is created using the default environment variables
_shared_client = WorkflowAIClient(
    endpoint=os.getenv("WORKFLOWAI_API_URL"),
    api_key=os.getenv("WORKFLOWAI_API_KEY", ""),
)


def init(api_key: str, url: Optional[str] = None):
    """Create a new workflowai client

    Args:
        url (Optional[str], optional): The API endpoint to use.
            If not provided, the env variable WORKFLOWAI_API_URL is used. Otherwise defaults to https://api.workflowai.com
        api_key (Optional[str], optional): _description_. If not provided, the env variable WORKFLOWAI_API_KEY is used.

    Returns:
        client.Client: a client instance
    """

    global _shared_client  # noqa: PLW0603
    _shared_client = WorkflowAIClient(endpoint=url, api_key=api_key)


def task(
    schema_id: int,
    task_id: Optional[str] = None,
    version: VersionReference = DEFAULT_VERSION_REFERENCE,
) -> TaskDecorator:
    return _shared_client.task(schema_id, task_id, version)
