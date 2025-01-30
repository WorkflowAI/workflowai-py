from collections.abc import Iterator
from typing import Callable, Iterable, Optional

from workflowai.core._logger import logger
from workflowai.core.utils._vars import T, U


def safe_map(iterable: Iterable[T], func: Callable[[T], U]) -> Iterator[U]:
    """Map 'iterable' with 'func' and return a list of results, ignoring any errors."""

    for item in iterable:
        try:
            yield func(item)
        except Exception as e:  # noqa: PERF203, BLE001
            logger.exception(e)


def safe_map_list(iterable: Optional[Iterable[T]], func: Callable[[T], U]) -> Optional[list[U]]:
    if not iterable:
        return None

    return list(safe_map(iterable, func))
