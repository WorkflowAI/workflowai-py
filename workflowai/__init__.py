from typing import Optional

from workflowai.core import client
from workflowai.core.domain.cache_usage import CacheUsage as CacheUsage
from workflowai.core.domain.errors import NotFoundError as NotFoundError
from workflowai.core.domain.task import Task as Task
from workflowai.core.domain.task_run import TaskRun as TaskRun
from workflowai.core.domain.task_version_reference import (
    TaskVersionReference as TaskVersionReference,
)


def start(
    endpoint: Optional[str] = None, api_key: Optional[str] = None
) -> "client.Client":
    from workflowai.core.client.client import WorkflowAIClient

    return WorkflowAIClient(endpoint, api_key)
