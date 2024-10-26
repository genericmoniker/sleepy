import datetime
import logging
import sys


def setup(level=logging.INFO):
    """Set up logging to stdout."""
    fmt = "{asctime} {levelname:8} {name}: {message}"
    formatter = ISO8601Formatter(fmt, style="{")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


class ISO8601Formatter(logging.Formatter):
    """Formatter to output ISO8601 date/time with milliseconds and timezone."""

    def formatTime(self, record, datefmt=None):
        return (
            datetime.datetime.fromtimestamp(record.created, datetime.UTC)
            .astimezone()
            .isoformat()
        )
