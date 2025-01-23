from typing import Literal, Union

from workflowai.core.domain.version_properties import VersionProperties

VersionEnvironment = Literal["dev", "staging", "production"]

VersionReference = Union[int, VersionEnvironment, VersionProperties]
