from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")
U = TypeVar("U")

BM = TypeVar("BM", bound=BaseModel)
