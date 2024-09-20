from pydantic import BaseModel, Field

from .html_string import HTMLString


class _ModelWithHMTLString(BaseModel):
    html_string: HTMLString = Field("A string that contains HTML.", examples=["<h1>Example</h1>"])


def test_html_string_json_schema() -> None:
    schema = _ModelWithHMTLString.model_json_schema()
    assert schema == {
        "properties": {
            "html_string": {
                "default": "A string that contains HTML.",
                "examples": ["<h1>Example</h1>"],
                "format": "html",
                "title": "Html String",
                "type": "string",
            },
        },
        "title": "_ModelWithHMTLString",
        "type": "object",
    }
