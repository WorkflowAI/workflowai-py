from typing import Any, AsyncIterator, Literal, Optional, Protocol, Union, overload

from workflowai.core.domain import cache_usage, task, task_run, task_version_reference


class Client(Protocol):
    async def register(self, task: "task.Task[task.TaskInput, task.TaskOutput]"): ...

    @overload
    async def run(
        self,
        task: "task.Task[task.TaskInput, task.TaskOutput]",
        task_input: "task.TaskInput",
        version: Optional["task_version_reference.TaskVersionReference"] = None,
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
        stream: bool = False,
        use_cache: "cache_usage.CacheUsage" = "when_available",
        labels: Optional[set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Union[
        "task_run.TaskRun[task.TaskInput, task.TaskOutput]",
        AsyncIterator["task.TaskOutput"],
    ]: ...
