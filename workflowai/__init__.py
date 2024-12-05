import os
from typing import Optional

from workflowai.core.client import Client as Client
from workflowai.core.domain.cache_usage import CacheUsage as CacheUsage
from workflowai.core.domain.errors import WorkflowAIError as WorkflowAIError
from workflowai.core.domain.run import Run as Run
from workflowai.core.domain.task import Task as Task
from workflowai.core.domain.task_version import TaskVersion as TaskVersion
from workflowai.core.domain.version_reference import (
    VersionReference as VersionReference,
)


def _build_client(
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    default_version: Optional[VersionReference] = None,
) -> Client:
    from workflowai.core.client.client import WorkflowAIClient

    return WorkflowAIClient(
        endpoint=endpoint or os.getenv("WORKFLOWAI_API_URL"),
        api_key=api_key or os.getenv("WORKFLOWAI_API_KEY", ""),
        default_version=default_version,
    )


# By default the shared client is created using the default environment variables
shared_client: Client = _build_client()


def init(api_key: Optional[str] = None, url: Optional[str] = None, default_version: Optional[VersionReference] = None):
    """Create a new workflowai client

    Args:
        url (Optional[str], optional): The API endpoint to use.
            If not provided, the env variable WORKFLOWAI_API_URL is used. Otherwise defaults to https://api.workflowai.com
        api_key (Optional[str], optional): _description_. If not provided, the env variable WORKFLOWAI_API_KEY is used.
        default_version (Optional[VersionReference], optional): The default version to use for tasks. If not provided,
            the env var 'WORKFLOWAI_DEFAULT_VERSION' is used. Defaults to production.
    Returns:
        client.Client: a client instance
    """

    global shared_client  # noqa: PLW0603
    shared_client = _build_client(url, api_key, default_version)


def task(
    schema_id: int,
    task_id: Optional[str] = None,
    version: Optional[VersionReference] = None,
):
    from workflowai.core.client._fn_utils import task_wrapper

    return task_wrapper(lambda: shared_client, schema_id, task_id, version)
