from typing import Literal, Union

VersionEnvironment = Literal["dev", "staging", "production"]

VersionReference = Union[int, VersionEnvironment]
