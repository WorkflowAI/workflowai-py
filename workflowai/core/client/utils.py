# Sometimes, 2 payloads are sent in a single message.
# By adding the " at the end we more or less guarantee that
# the delimiter is not withing a quoted string
import asyncio
import re
from email.utils import parsedate_to_datetime
from time import time
from typing import Any, Optional

from httpx import HTTPStatusError

delimiter = re.compile(r'\}\n\ndata: \{"')


def split_chunks(chunk: bytes):
    start = 0
    chunk_str = chunk.removeprefix(b"data: ").removesuffix(b"\n\n").decode()
    for match in delimiter.finditer(chunk_str):
        yield chunk_str[start : match.start() + 1]
        start = match.end() - 2
    yield chunk_str[start:]


def retry_after_to_delay_seconds(retry_after: Any) -> Optional[float]:
    if retry_after is None:
        return None

    try:
        return float(retry_after)
    except ValueError:
        pass
    try:
        retry_after_date = parsedate_to_datetime(retry_after)
        current_time = time()
        return retry_after_date.timestamp() - current_time
    except (TypeError, ValueError, OverflowError):
        return None


# Returns two functions:
# - _should_retry: returns True if we should retry
# - _wait_for_exception: waits after an exception only if we should retry, otherwise raises
# This is a bit convoluted and would be better in a function wrapper, but since we are dealing
# with both Awaitable and AsyncGenerator, a wrapper would just be too complex
def build_retryable_wait(
    max_retry_delay: float = 60,
    max_retry_count: float = 1,
):
    now = time()
    retry_count = 0

    def _leftover_delay():
        # Time remaining before we hit the max retry delay
        return max_retry_delay - (time() - now)

    def _should_retry():
        return retry_count < max_retry_count and _leftover_delay() >= 0

    async def _wait_for_exception(e: HTTPStatusError):
        nonlocal retry_count
        retry_after = retry_after_to_delay_seconds(e.response.headers.get("Retry-After"))
        leftover_delay = _leftover_delay()
        if not retry_after or leftover_delay < 0 or retry_count >= max_retry_count:
            # TODO: convert error to WorkflowAIError
            raise e
        await asyncio.sleep(retry_after)
        retry_count += 1

    return _should_retry, _wait_for_exception
