# Sometimes, 2 payloads are sent in a single message.
# By adding the " at the end we more or less guarantee that
# the delimiter is not withing a quoted string
import re

delimiter = re.compile(r'\}\n\ndata: \{"')


def split_chunks(chunk: bytes):
    start = 0
    chunk_str = chunk.removeprefix(b"data: ").removesuffix(b"\n\n").decode()
    for match in delimiter.finditer(chunk_str):
        yield chunk_str[start : match.start() + 1]
        start = match.end() - 2
    yield chunk_str[start:]
