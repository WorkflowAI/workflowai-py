from pydantic import BaseModel, Field


class Image(BaseModel):
    name: str = Field(..., description="An optional name for the image")
    content_type: str = Field(..., description="The content type of the image", examples=["image/png", "image/jpeg"])
    data: str = Field(..., description="The base64 encoded data of the image")

    def to_url(self) -> str:
        return f"data:{self.content_type};base64,{self.data}"
