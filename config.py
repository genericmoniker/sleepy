from dataclasses import dataclass, field
import os
from pathlib import Path


def env_field(env_var: str, default: str) -> field:
    """Return a field with the value of an environment variable or a default value."""
    return field(default_factory=lambda: os.environ.get(env_var, default))


@dataclass
class Config:
    config_path: Path = Path(__file__).parent / ".instance"
    time_zone: str = env_field("TZ", "America/Denver")
    update_data_time: str = env_field("UPDATE_DATA_TIME", "08:00")

    fitbit_creds: Path = config_path / "fitbit.json"
    google_creds: Path = config_path / "google.json"

    db_token: str = env_field("INFLUXDB_TOKEN", "")
    db_url: str = env_field("INFLUXDB_URL", "http://localhost:8086")
    db_org: str = env_field("INFLUXDB_ORG", "sleepy")
    db_bucket: str = env_field("INFLUXDB_BUCKET", "sleepy")
