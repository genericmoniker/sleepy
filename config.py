import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


def env_field(
    env_var: str, default: str, cast: Callable[[str], Any] | None = None
) -> field:
    """Return a field with the value of an environment variable or a default value.

    If `cast` is not None, the value will be cast to the type of `cast`.
    """

    def factory():
        value = os.environ.get(env_var, default)
        if cast is not None:
            value = cast(value)
        return value

    return field(default_factory=factory)


@dataclass()
class Config:
    config_path: Path = env_field(
        "INSTANCE_PATH", str(Path(__file__).parent / ".instance"), Path
    )
    time_zone: str = env_field("TZ", "America/Denver")
    update_data_time: str = env_field("UPDATE_DATA_TIME", "08:00")

    fitbit_creds: Path = None
    google_creds: Path = None

    db_token: str = env_field("INFLUXDB_TOKEN", "")
    db_url: str = env_field("INFLUXDB_URL", "http://localhost:8086")
    db_org: str = env_field("INFLUXDB_ORG", "sleepy")
    db_bucket: str = env_field("INFLUXDB_BUCKET", "sleepy")

    def __post_init__(self):
        self.fitbit_creds = self.config_path / "fitbit.json"
        self.google_creds = self.config_path / "google.json"
