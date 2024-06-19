import pytest
from pydantic import BaseModel

from .http_url import HttpUrl


class ModelWithHttpUrl(BaseModel):
    url: HttpUrl


def test_http_url_json_schema() -> None:
    schema = ModelWithHttpUrl.model_json_schema()
    assert schema == {
        "properties": {
            "url": {
                "format": "url",
                "title": "Url",
                "type": "string",
                "examples": ["http://www.example.com"],
            }
        },
        "required": ["url"],
        "title": "ModelWithHttpUrl",
        "type": "object",
    }


def test_http_url_serialize() -> None:
    model = ModelWithHttpUrl(url="http://example.com")
    assert model.model_dump() == {"url": "http://example.com"}


def test_URL_value() -> None:
    """Test that the HttpUrl validates the URL value."""

    # Should raise
    for invalid_url in ["http://", "https://", "http://example", "https://example"]:
        with pytest.raises(ValueError):
            ModelWithHttpUrl(url=invalid_url)

    # Should not raise
    for valid_url in [
        "http://example.com",
        "https://example.com",
        "http://www.example.com",
        "https://www.example.com",
    ]:
        ModelWithHttpUrl(url=valid_url)


def test_validates_URL_scheme() -> None:
    """Tests that the HttpUrl field only accepts URLs with the http or https scheme."""

    # Should raise
    for non_http_url in [
        "ftp://example.com",
        "file://example.com",
        "sftp://example.com",
    ]:
        with pytest.raises(ValueError):
            ModelWithHttpUrl(url=non_http_url)

    # Should not raise
    for http_url in ["http://example.com", "https://example.com"]:
        ModelWithHttpUrl(url=http_url)
