"""Application paths."""

from pathlib import Path

INSTANCE_DIR = Path(__file__).parent.parent.parent / "instance"
FITBIT_CREDS = INSTANCE_DIR / "fitbit.json"
GOOGLE_CREDS = INSTANCE_DIR / "google-credentials.json"
GOOGLE_AUTH = INSTANCE_DIR / "google-authorized-user.json"
