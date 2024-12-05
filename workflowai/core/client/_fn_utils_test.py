from typing import AsyncIterator

from pydantic import BaseModel

from tests.models.hello_task import HelloTaskInput, HelloTaskOutput
from workflowai.core.client._fn_utils import extract_fn_data, get_generic_args, is_async_iterator
from workflowai.core.domain.run import Run


async def say_hello(task_input: HelloTaskInput) -> HelloTaskOutput: ...


async def say_hello_run(task_input: HelloTaskInput) -> Run[HelloTaskOutput]: ...


def stream_hello(task_input: HelloTaskInput) -> AsyncIterator[HelloTaskOutput]: ...


def stream_hello_run(task_input: HelloTaskInput) -> AsyncIterator[Run[HelloTaskOutput]]: ...


class TestGetGenericArgs:
    def test_get_generic_arg(self):
        assert get_generic_args(Run[HelloTaskOutput]) == (HelloTaskOutput,)


class TestIsAsyncIterator:
    def test_is_async_iterator(self):
        assert is_async_iterator(AsyncIterator[HelloTaskOutput])
        assert not is_async_iterator(HelloTaskOutput)
        assert not is_async_iterator(BaseModel)


class TestExtractFnData:
    def test_run_output_only(self):
        assert extract_fn_data(say_hello) == (False, True, HelloTaskInput, HelloTaskOutput)

    def test_run(self):
        assert extract_fn_data(say_hello_run) == (False, False, HelloTaskInput, HelloTaskOutput)

    def test_stream_output_only(self):
        assert extract_fn_data(stream_hello) == (True, True, HelloTaskInput, HelloTaskOutput)

    def test_stream(self):
        assert extract_fn_data(stream_hello_run) == (True, False, HelloTaskInput, HelloTaskOutput)
