from typing import Any, AsyncIterator, Literal, Optional, Protocol, Union, overload

from workflowai.core.domain.cache_usage import CacheUsage
from workflowai.core.domain.task import Task, TaskInput, TaskOutput
from workflowai.core.domain.task_run import Run, RunChunk
from workflowai.core.domain.task_version_reference import VersionReference


class Client(Protocol):
    """A client to interact with the WorkflowAI API"""

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: Literal[False] = False,
        version: Optional[VersionReference] = None,
        use_cache: CacheUsage = "when_available",
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> Run[TaskOutput]: ...

    @overload
    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: Literal[True] = True,
        version: Optional[VersionReference] = None,
        use_cache: CacheUsage = "when_available",
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> AsyncIterator[Union[RunChunk[TaskOutput], Run[TaskOutput]]]: ...

    async def run(
        self,
        task: Task[TaskInput, TaskOutput],
        task_input: TaskInput,
        stream: bool = False,
        version: Optional[VersionReference] = None,
        use_cache: CacheUsage = "when_available",
        metadata: Optional[dict[str, Any]] = None,
        max_retry_delay: float = 60,
        max_retry_count: float = 1,
    ) -> Union[Run[TaskOutput], AsyncIterator[Union[RunChunk[TaskOutput], Run[TaskOutput]]]]:
        """Run a task

        Args:
            task (Task[TaskInput, TaskOutput]): the task to run
            task_input (TaskInput): the input to the task
            version (Optional[TaskVersionReference], optional): the version of the task to run. If not provided,
                the version defined in the task is used. Defaults to None.
            environment (Optional[str], optional): the environment to run the task in. If not provided, the environment
                defined in the task is used. Defaults to None.
            iteration (Optional[int], optional): the iteration of the task to run. If not provided, the iteration
                defined in the task is used. Defaults to None.
            stream (bool, optional): whether to stream the output. If True, the function returns an async iterator of
                partial output objects. Defaults to False.
            use_cache (CacheUsage, optional): how to use the cache. Defaults to "when_available".
            labels (Optional[set[str]], optional): a set of labels to attach to the run.
                Labels are indexed and searchable. Defaults to None.
            metadata (Optional[dict[str, Any]], optional): a dictionary of metadata to attach to the run.
                Defaults to None.
            retry_delay (int, optional): The initial delay between retries in milliseconds. Defaults to 5000.
            max_retry_delay (int, optional): The maximum delay between retries in milliseconds. Defaults to 60000.
            max_retry_count (int, optional): The maximum number of retry attempts. Defaults to 1.

        Returns:
            Union[TaskRun[TaskInput, TaskOutput], AsyncIterator[TaskOutput]]: the task run object
                or an async iterator of output objects
        """
        ...
