from typing import Annotated

from pydantic import WithJsonSchema

HTMLString = Annotated[
    str,
    WithJsonSchema(
        {
            "type": "string",
            "format": "html",
        },
    ),
]
