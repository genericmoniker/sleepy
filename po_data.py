"""Pulse Oximeter Data Module."""

import csv
import json
import logging
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from zoneinfo import ZoneInfo

from config import Config
from database import Database
from utils import timestamp_to_utc

logger = logging.getLogger(__name__)


def update(config: Config, db: Database) -> None:
    """Update data from the pulse oximeter CSV stored in Google Drive."""
    try:
        with config.google_creds.open() as creds_file:
            creds_data = json.load(creds_file)
            creds = Credentials(
                token=creds_data["access_token"],
                refresh_token=creds_data["refresh_token"],
                token_uri=creds_data["token_uri"],
                client_id=creds_data["client_id"],
                client_secret=creds_data["client_secret"],
                scopes=creds_data["scopes"],
            )
            service = build("drive", "v3", credentials=creds)
            last_date = db.get_latest_spo2_date(source="EMAY")
            data = _fetch_spo2_and_pulse_rate(service, last_date)
        _store_spo2_and_pulse_rate(config.time_zone, db, data)

        # Save potentially updated credentials.
        with config.google_creds.open("w") as creds_file:
            creds_file.write(
                json.dumps(
                    {
                        "access_token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "token_uri": creds.token_uri,
                        "client_id": creds.client_id,
                        "client_secret": creds.client_secret,
                        "scopes": creds.scopes,
                    }
                )
            )

    except Exception:
        logger.exception("Error updating data from the pulse oximeter CSV.")


def _fetch_spo2_and_pulse_rate(service, since: datetime | None) -> list[dict]:
    """Fetch SpO2 and pulse rate data from the pulse oximeter CSV files."""
    folder_name = "SpO2"
    folder_query = (
        f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
    )
    folder_results = (
        service.files().list(q=folder_query, fields="files(id, name)").execute()
    )
    folders = folder_results.get("files", [])

    if not folders:
        logger.error(f"Google Drive folder '{folder_name}' not found.")
        return []

    folder_id = folders[0]["id"]

    # Search for files in the folder
    query = f"'{folder_id}' in parents and name contains '.csv'"
    if since:
        query += f" and modifiedTime > '{since.isoformat()}'"

    results = (
        service.files().list(q=query, pageSize=100, fields="files(id, name)").execute()
    )
    files = results.get("files", [])

    # Fetch the file contents and parse the data.
    measurements = []
    for file in files:
        file_id = file["id"]
        request = service.files().get_media(fileId=file_id)
        content = request.execute()
        csv_data = content.decode("utf-8").splitlines()
        reader = csv.DictReader(csv_data)
        for row in reader:
            timestamp = datetime.strptime(
                row["Date"] + " " + row["Time"], "%m/%d/%Y %I:%M:%S %p"
            )
            try:
                measurements.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "spo2": float(row["SpO2(%)"]),
                        "pulse": int(row["PR(bpm)"]),
                    }
                )
            except ValueError:
                logger.warning(
                    "Invalid or missing data in row: %s %s %s %s",
                    row["Date"],
                    row["Time"],
                    row["SpO2(%)"],
                    row["PR(bpm)"],
                )
    return measurements


def _store_spo2_and_pulse_rate(time_zone, db: Database, data: list[dict]) -> None:
    """Store the SpO2 and pulse rate data in the database."""
    zone_info = ZoneInfo(time_zone)
    source = "EMAY"
    with db.batch() as batch:
        for entry in data:
            timestamp = timestamp_to_utc(entry["timestamp"], zone_info)
            batch.add_pulse_measurement(timestamp, entry["pulse"], source)
            batch.add_spo2_measurement(timestamp, entry["spo2"], source)
    logger.info(
        "Stored %d records of SpO2 and pulse measurements from %s.", len(data), source
    )
