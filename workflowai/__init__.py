from typing import Optional

from workflowai.core.client import Client as Client
from workflowai.core.domain.cache_usage import CacheUsage as CacheUsage
from workflowai.core.domain.errors import NotFoundError as NotFoundError
from workflowai.core.domain.llm_completion import LLMCompletion as LLMCompletion
from workflowai.core.domain.task import Task as Task
from workflowai.core.domain.task_evaluation import TaskEvaluation as TaskEvaluation
from workflowai.core.domain.task_example import TaskExample as TaskExample
from workflowai.core.domain.task_run import TaskRun as TaskRun
from workflowai.core.domain.task_version import TaskVersion as TaskVersion
from workflowai.core.domain.task_version_reference import (
    TaskVersionReference as TaskVersionReference,
)


def start(url: Optional[str] = None, api_key: Optional[str] = None) -> Client:
    """Create a new workflowai client

    Args:
        url (Optional[str], optional): The API endpoint to use.
            If not provided, the env variable WORKFLOWAI_API_URL is used. Otherwise defaults to https://api.workflowai.com
        api_key (Optional[str], optional): _description_. If not provided, the env variable WORKFLOWAI_API_KEY is used.

    Returns:
        client.Client: a client instance
    """
    from workflowai.core.client.client import WorkflowAIClient

    return WorkflowAIClient(url, api_key)
