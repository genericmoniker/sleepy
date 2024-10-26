"""Data storage using InfluxDB.

InfluxDB version note: This code uses InfluxDB 2. At the time of writing, InfluxDB 3,
which is a rewrite of InfluxDB in Rust, hasn't been released. If it seems like an
interesting thing to upgrade at some point, Flux queries will no longer be supported, so
they'll need to be converted to InfluxQL queries. Even though InfluxQL is supported in
InfluxDB 2, it is kind of awkward.

Python client API documentation:
https://influxdb-client.readthedocs.io/en/stable/api.html
"""

from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from zoneinfo import ZoneInfo

from config import Config


class Database:
    """Interface for persistently writing measurements."""

    def __init__(self, config: Config) -> None:
        token = config.db_token
        url = config.db_url
        org = config.db_org
        self.bucket = config.db_bucket
        self.timezone = ZoneInfo(config.time_zone)
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.query = self.client.query_api().query
        self._records = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.__exit__(exc_type, exc_value, traceback)

    def batch(self) -> "_Batch":
        """Return a batch object for batch writing."""
        return _Batch(self.client, self.bucket)

    def get_latest_spo2_date(self, source: str) -> datetime | None:
        """Return the most recent date for which SpO2 data has been stored."""
        query = (
            f'from(bucket: "{self.bucket}") '
            "|> range(start: 0) "
            f'|> filter(fn: (r) => r._measurement == "spo2" and r.source == "{source}") '
            "|> last()"
        )
        tables = self.query(query=query)
        output = tables.to_values(columns=["_time"])
        if output:
            return output[0][0]
        return None


class _Batch:
    """Batch writes to InfluxDB.

    This is a context manager that batches writes to InfluxDB. The batch is written when
    the context manager exits. This is useful when writing a large number of records to
    InfluxDB, as it reduces the number of HTTP requests made to the server.
    """

    def __init__(self, client: InfluxDBClient, bucket: str) -> None:
        self.client = client
        self.bucket = bucket
        # I think this is configured (by default) to write in "batch mode", but the
        # documentation and examples are unclear.
        self.write_api = client.write_api()
        self._records = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.write_api.write(bucket=self.bucket, record=self._records)
        self.write_api.__exit__(exc_type, exc_value, traceback)
        self._records.clear()

    def add_spo2_measurement(
        self, timestamp: datetime, spo2: float, source: str
    ) -> None:
        """Add a pending SpO2 measurements to the database.

        `timestamp` is a datetime object in UTC.
        `spo2` is the SpO2 value as a percentage (0.0-100.0).
        `source` is the source of the data.
        """
        point = (
            Point("spo2")
            .tag("source", source)
            .field("spo2", spo2)
            .time(timestamp, WritePrecision.S)
        )
        self._records.append(point)
