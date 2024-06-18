from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest
from pydantic import BaseModel

from .local_date_time import DatetimeLocal


@pytest.mark.parametrize(
    "date, local_time, timezone, expected_datetime",
    [
        (
            date(2022, 5, 15),
            time(15, 30),  # time without timezone
            "Europe/London",
            datetime(2022, 5, 15, 15, 30, tzinfo=ZoneInfo("Europe/London")),
        ),
        (
            date(2022, 12, 25),
            time(23, 59),  # time without timezone
            "Asia/Tokyo",
            datetime(2022, 12, 25, 23, 59, tzinfo=ZoneInfo("Asia/Tokyo")),
        ),
        (
            date(2022, 1, 1),
            time(1, 0, tzinfo=ZoneInfo("America/New_York")),  # time with timezone
            "America/New_York",
            datetime(2022, 1, 1, 1, 0, tzinfo=ZoneInfo("America/New_York")),
        ),
    ],
)
def test_datetime_local_to_datetime_parametrized(
    date: date, local_time: time, timezone: str, expected_datetime: datetime
) -> None:
    """Test 'datetime_local_to_datetime' function. It should return a 'datetime' object from DatetimeLocal object."""

    datetime_local_instance = DatetimeLocal(date=date, local_time=local_time, timezone=ZoneInfo(timezone))
    assert datetime_local_instance.to_datetime() == expected_datetime


class ModelWithDatetimeLocal(BaseModel):
    local_datetime: DatetimeLocal


def test_local_date_time_json_schema() -> None:
    schema = ModelWithDatetimeLocal.model_json_schema()
    assert schema == {
        "$defs": {
            "DatetimeLocal": {
                "description": "This class represents a local datetime, with a datetime and a timezone.",
                "properties": {
                    "date": {
                        "description": "The date of the local datetime.",
                        "examples": ["2023-03-01"],
                        "format": "date",
                        "title": "Date",
                        "type": "string",
                    },
                    "local_time": {
                        "description": "The time of the local datetime without timezone info.",
                        "examples": ["12:00:00", "22:00:00"],
                        "format": "time",
                        "title": "Local Time",
                        "type": "string",
                    },
                    "timezone": {
                        "description": "The timezone of the local time.",
                        "examples": ["Europe/Paris", "America/New_York"],
                        "format": "timezone",
                        "title": "Timezone",
                        "type": "string",
                    },
                },
                "required": ["date", "local_time", "timezone"],
                "title": "DatetimeLocal",
                "type": "object",
            }
        },
        "properties": {"local_datetime": {"$ref": "#/$defs/DatetimeLocal"}},
        "required": ["local_datetime"],
        "title": "ModelWithDatetimeLocal",
        "type": "object",
    }


def test_local_date_time_dump_sanity() -> None:
    model = ModelWithDatetimeLocal(
        local_datetime=DatetimeLocal(
            date=date(2022, 5, 15),
            local_time=time(15, 30),
            timezone=ZoneInfo("Europe/London"),
        )
    )
    dumped = model.model_dump()
    assert dumped == {
        "local_datetime": {
            "date": date(2022, 5, 15),
            "local_time": time(15, 30),
            "timezone": "Europe/London",
        }
    }

    sanity = ModelWithDatetimeLocal.model_validate(dumped)
    assert sanity == model
