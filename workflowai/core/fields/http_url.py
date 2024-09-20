import re
import urllib.parse
from typing import Annotated

from pydantic import (
    AfterValidator,
    WithJsonSchema,
)


def parse_url(url: str) -> tuple[str, str, str, dict[str, list[str]]]:
    """Extract the four components of a URL (schema, domain, path, and query)."""

    parsed_url = urllib.parse.urlparse(url)

    # Extract the four components of the URL
    schema, domain, path, query = (
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        urllib.parse.parse_qs(parsed_url.query),
    )

    # Remove trailing slashes
    path = path.rstrip("/")

    return schema, domain, path, query


def is_valid_http_url(value: str) -> bool:
    """
    Validates a URL string to ensure it is a well-formed URL with either http or https scheme,
    contains a valid domain with a TLD.

    Parameters:
    - value (str): The URL string to validate.

    Returns:
    - str: The validated URL string if it is valid.

    Raises:
    - ValueError: If the URL is not valid, the scheme is not http or https, or the domain is missing or invalid.
    """
    try:
        schema, domain, _, _ = parse_url(value)  # Use urlparse to parse the URL
        if schema not in {"http", "https"}:
            return False  # Invalid schema
        if not domain:
            raise ValueError("URL must have a domain")

        # Regular expression for validating domain with TLD
        domain_regex = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$",
        )
        if not domain_regex.match(domain):
            return False  # Invalid domain (no TLD or invalid characters in domain name)

    except ValueError:
        return False  # URL is not parsable

    return True


def _validate_http_url(url: str) -> str:
    if not is_valid_http_url(url):
        raise ValueError("Invalid URL")

    return url


HttpUrl = Annotated[
    str,
    AfterValidator(_validate_http_url),
    WithJsonSchema(
        {"format": "url", "type": "string", "examples": ["http://www.example.com"]},
    ),
]
