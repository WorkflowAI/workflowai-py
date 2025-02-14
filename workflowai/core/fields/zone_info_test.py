from zoneinfo import ZoneInfo

from pydantic import BaseModel

from .zone_info import TimezoneInfo


class ModelWithTimezone(BaseModel):
    timezone: TimezoneInfo


def test_timezone_info_schema() -> None:
    schema = ModelWithTimezone.model_json_schema()
    assert schema == {
        "properties": {"timezone": {"title": "Timezone", "type": "string", "format": "timezone"}},
        "required": ["timezone"],
        "title": "ModelWithTimezone",
        "type": "object",
    }


def test_timezone_info_dump() -> None:
    model = ModelWithTimezone(timezone=ZoneInfo("Europe/Paris"))
    assert model.model_dump() == {"timezone": "Europe/Paris"}
