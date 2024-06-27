from typing import Any, AsyncIterator, Literal, Optional, Protocol, Union, overload

from workflowai.core.domain import (
    cache_usage,
    page,
    task,
    task_example,
    task_run,
    task_version,
    task_version_reference,
)


class Client(Protocol):
    """A client to interact with the WorkflowAI API"""

    async def register(self, task: "task.Task[task.TaskInput, task.TaskOutput]"):
        """Register a task, creating a new task if needed and setting the task schema id

        Args:
            task (task.Task[task.TaskInput, task.TaskOutput]): a task
        """
        ...

    @overload
    async def run(
        self,
        task: "task.Task[task.TaskInput, task.TaskOutput]",
        task_input: "task.TaskInput",
        version: Optional["task_version_reference.TaskVersionReference"] = None,
        environment: Optional[str] = None,
        iteration: Optional[int] = None,
        stream: Literal[False] = False,
        use_cache: "cache_usage.CacheUsage" = "when_available",
        labels: Optional[set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "task_run.TaskRun[task.TaskInput, task.TaskOutput]": ...

    @overload
    async def run(
        self,
        task: "task.Task[task.TaskInput, task.TaskOutput]",
        task_input: "task.TaskInput",
        version: Optional["task_version_reference.TaskVersionReference"] = None,
        environment: Optional[str] = None,
        iteration: Optional[int] = None,
        stream: Literal[True] = True,
        use_cache: "cache_usage.CacheUsage" = "when_available",
        labels: Optional[set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator["task.TaskOutput"]: ...

    async def run(
        self,
        task: "task.Task[task.TaskInput, task.TaskOutput]",
        task_input: "task.TaskInput",
        version: Optional["task_version_reference.TaskVersionReference"] = None,
        environment: Optional[str] = None,
        iteration: Optional[int] = None,
        stream: bool = False,
        use_cache: "cache_usage.CacheUsage" = "when_available",
        labels: Optional[set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Union[
        "task_run.TaskRun[task.TaskInput, task.TaskOutput]",
        AsyncIterator["task.TaskOutput"],
    ]:
        """Run a task

        Args:
            task (Task[TaskInput, TaskOutput]): the task to run
            task_input (TaskInput): the input to the task
            version (Optional[TaskVersionReference], optional): the version of the task to run. If not provided, the version defined in the task is used. Defaults to None.
            stream (bool, optional): whether to stream the output. If True, the function returns an async iterator of partial output objects. Defaults to False.
            use_cache (CacheUsage, optional): how to use the cache. Defaults to "when_available".
            labels (Optional[set[str]], optional): a set of labels to attach to the run. Labels are indexed and searchable. Defaults to None.
            metadata (Optional[dict[str, Any]], optional): a dictionary of metadata to attach to the run. Defaults to None.

        Returns:
            Union[TaskRun[TaskInput, TaskOutput], AsyncIterator[TaskOutput]]: the task run object or an async iterator of output objects
        """
        ...

    async def import_run(
        self, run: "task_run.TaskRun[task.TaskInput, task.TaskOutput]"
    ) -> "task_run.TaskRun[task.TaskInput, task.TaskOutput]":
        """Import a task run

        Args:
            run (task_run.TaskRun[task.TaskInput, task.TaskOutput]): a task run

        Returns:
            task_run.TaskRun[task.TaskInput, task.TaskOutput]: the task run as stored in our database
        """
        ...

    async def import_example(
        self, example: "task_example.TaskExample[task.TaskInput, task.TaskOutput]"
    ) -> "task_example.TaskExample[task.TaskInput, task.TaskOutput]":
        """Import a task example

        Args:
            example (task_example.TaskExample[task.TaskInput, task.TaskOutput]): a task example

        Returns:
            task_example.TaskExample[task.TaskInput, task.TaskOutput]: the task example as stored in our database
        """
        ...

    async def list_examples(
        self,
        task: "task.Task[task.TaskInput, task.TaskOutput]",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> "page.Page[task_example.TaskExample[task.TaskInput, task.TaskOutput]]":
        """List examples for a task

        Args:
            task (task.Task[task.TaskInput, task.TaskOutput]): the task
            limit (Optional[int], optional): the maximum number of examples to return. Defaults to None.
            offset (Optional[int], optional): the number of examples to skip. Defaults to None.

        Returns:
            page.Page[task_example.TaskExample[task.TaskInput, task.TaskOutput]]: a page of examples
        """
        ...

    async def deploy_version(
        self,
        task: "task.Task[task.TaskInput, task.TaskOutput]",
        iteration: int,
        environment: str,
    ) -> "task_version.TaskVersion":
        """Deploy a version to an environemnt. Version becomes usable using TaskVersionReference(environment=...)

        Args:
            task (task.Task[task.TaskInput, task.TaskOutput]): the task to deploy
            reference (task_version_reference.TaskVersionReference): the version to deploy
            environment (str): the environment to deploy to

        Returns:
            task_version.TaskVersion: the deployed version
        """
        ...
