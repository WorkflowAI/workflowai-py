import re
from typing import Annotated

from pydantic import AfterValidator, WithJsonSchema

_email_regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


def _validate_email_str(v: str) -> str:
    if not _email_regex.match(v):
        raise ValueError(f"Invalid email format: {v}")
    # Additional checks for edge cases not covered by regex
    local_part, domain_part = v.split("@")
    if local_part.startswith(".") or local_part.endswith("."):
        raise ValueError(f"Invalid email format: :{v}, local part starts or ends with a dot ")
    if ".." in local_part or ".." in domain_part:
        raise ValueError("Invalid email format: consecutive dots")
    if domain_part.startswith("-") or domain_part.endswith("."):
        raise ValueError(f"Invalid email format: :{v}, domain part starts with a hyphen or ends with a dot")
    if any(segment == "" for segment in domain_part.split(".")):
        raise ValueError("Invalid email format: :{v}, domain part has consecutive dots")
    return v


# Use instead of str in pydantic models to add extra validation and schema fields for email
EmailAddressStr = Annotated[
    str,
    AfterValidator(_validate_email_str),
    WithJsonSchema(
        {"format": "email", "type": "string", "examples": ["john.doe@example.com"]},
    ),
]
