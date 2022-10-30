from datetime import datetime

import pytz


def utc_to_local(v: datetime, timezone: str) -> datetime:
    """
    convert utc time into given local timezone,
    will return datetime without a tzinfo
    """
    time_zone = pytz.timezone(timezone)
    return pytz.utc.localize(v).astimezone(time_zone).replace(tzinfo=None)


def local_to_utc(v: datetime, timezone: str) -> datetime:
    """
    convert datetime from given local timzone into utc,
    will return datetime without a tzinfo
    """
    time_zone = pytz.timezone(timezone)
    return time_zone.localize(v).astimezone(pytz.utc).replace(tzinfo=None)


def form_field_to_datetime(value: str | None) -> datetime | None:
    """
    Handle loading a datetime from form input

        :param value: The form value
        :return: The processed datetime or None
    """
    if value:
        return datetime.fromisoformat(value)
