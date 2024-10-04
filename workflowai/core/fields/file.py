from typing import Optional

from pydantic import BaseModel, Field, model_validator


class File(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="An optional name for the file [no longer used]",
        deprecated=True,
    )
    content_type: Optional[str] = Field(
        default=None,
        description="The content type of the file. Not needed if content type can be inferred from the URL.",
        examples=["image/png", "image/jpeg"],
    )
    data: Optional[str] = Field(
        default=None,
        description="The base64 encoded data of the file. Required if no URL is provided.",
    )
    url: Optional[str] = Field(
        default=None,
        description="The URL of the file. Required if no data is provided.",
    )

    def to_url(self) -> str:
        return f"data:{self.content_type};base64,{self.data}"

    @model_validator(mode="after")
    def validate_data_or_url(self):
        if self.url is None and (self.data is None or self.content_type is None):
            raise ValueError("Either data or url must be provided")
        return self
