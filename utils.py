from datetime import datetime
from zoneinfo import ZoneInfo


def timestamp_to_utc(timestamp: str, zone_info: ZoneInfo) -> datetime:
    """Convert a local timestamp string to a datetime object in UTC.

    `zone_info` is a ZoneInfo object representing the local time zone.
    """
    parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    return parsed.replace(tzinfo=zone_info).astimezone(ZoneInfo("UTC"))
