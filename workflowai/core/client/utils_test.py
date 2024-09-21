import pytest

from workflowai.core.client.utils import split_chunks


@pytest.mark.parametrize(
    ("chunk", "expected"),
    [
        (b'data: {"foo": "bar"}\n\ndata: {"foo": "baz"}', ['{"foo": "bar"}', '{"foo": "baz"}']),
        (
            b'data: {"foo": "bar"}\n\ndata: {"foo": "baz"}\n\ndata: {"foo": "qux"}',
            ['{"foo": "bar"}', '{"foo": "baz"}', '{"foo": "qux"}'],
        ),
    ],
)
def test_split_chunks(chunk: bytes, expected: list[bytes]):
    assert list(split_chunks(chunk)) == expected
