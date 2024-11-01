"""Processing for Fitbit data."""

from datetime import UTC, datetime, timedelta
import json
import logging
from zoneinfo import ZoneInfo

from httpx import HTTPStatusError
from config import Config
from database import Database
from fitbit_api import get_spo2
from utils import timestamp_to_utc

logger = logging.getLogger(__name__)


def update(config: Config, db: Database) -> None:
    """Update the data from Fitbit."""
    try:
        with config.fitbit_creds.open() as creds_file:
            creds = json.load(creds_file)
            last_date = db.get_latest_spo2_date(source="Fitbit")
            data = _fetch_spo2(creds, last_date)
            _store_spo2(config.time_zone, db, data)

            # TODO: Heart rate data?

        # Save potentially updated credentials.
        with config.fitbit_creds.open("w") as creds_file:
            creds_file.write(json.dumps(creds))
    except FileNotFoundError:
        logger.error("Fitbit credentials file not found. Setup is required.")
    except HTTPStatusError as ex:
        logger.exception("HTTP error updating data from Fitbit: %s", ex.response.text)
    except Exception:
        logger.exception("Error updating data from Fitbit.")


def _fetch_spo2(creds: dict, since: datetime | None) -> list[dict]:
    """Fetch SpO2 data from the Fitbit API."""
    if since:
        begin = min(since + timedelta(days=1), datetime.now(tz=UTC))
        # TODO: Handle the case where the range here exceeds the 30-day limit.
        return get_spo2(creds, begin)

    # If we don't have any data locally, backfill it.
    # The API limits the range to 30 days, so we need to fetch data in chunks, walking
    # back from the current date until we don't get back any data.
    logger.info("Backfilling historical SpO2 data from Fitbit.")
    end = datetime.now()
    begin = end - timedelta(days=14)
    data = []
    while True and begin > datetime(2024, 8, 1):  # TODO remove "and" part after testing
        chunk = get_spo2(creds, begin, end)
        if not chunk:
            logger.info("Backfilled to %s.", begin)
            break
        data.extend(chunk)
        end = begin - timedelta(days=1)
        begin = end - timedelta(days=14)
    return data


def _store_spo2(timezone: str, db: Database, data: list[dict]) -> None:
    """Store the SpO2 data in the database."""
    zone_info = ZoneInfo(timezone)
    source = "Fitbit"
    with db.batch() as batch:
        for day in data:
            for item in day["minutes"]:
                timestamp = timestamp_to_utc(item["minute"], zone_info)
                spo2 = item["value"]
                batch.add_spo2_measurement(timestamp, spo2, source)
    logger.info("Stored %d day(s) of SpO2 measurements from %s.", len(data), source)
