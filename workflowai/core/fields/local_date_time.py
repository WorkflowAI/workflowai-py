import datetime

from pydantic import BaseModel, Field

from .zone_info import TimezoneInfo


class DatetimeLocal(BaseModel):
    """This class represents a local datetime, with a datetime and a timezone."""

    date: datetime.date = Field(
        description="The date of the local datetime.",
        examples=["2023-03-01"],
        json_schema_extra={"format": "date"},
    )
    local_time: datetime.time = Field(
        description="The time of the local datetime without timezone info.",
        examples=["12:00:00", "22:00:00"],
        json_schema_extra={"format": "time"},
    )
    timezone: TimezoneInfo = Field(
        description="The timezone of the local time.",
        examples=["Europe/Paris", "America/New_York"],
    )

    def to_datetime(self) -> datetime.datetime:
        """Builds a 'datetime' object from the local 'date', local 'time' and 'timezone'."""

        time_with_tz = self.local_time.replace(tzinfo=self.timezone)
        datetime_with_tz = datetime.datetime.combine(self.date, time_with_tz)
        return datetime_with_tz
