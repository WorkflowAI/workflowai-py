from enum import Enum

from pydantic import BaseModel, Field


class SurfaceArea(BaseModel):
    value: float = Field(description="The value of the surface area.", examples=["1506.7"])

    class Unit(Enum):
        SQFT = "SQFT"  # Square Foot
        SQM = "SQM"  # Square Meter

    unit: Unit = Field(
        description="The unit of the surface area.",
        examples=["SQFT", "SQM"],
    )
