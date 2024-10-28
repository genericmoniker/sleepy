"""Configure authentication for the Fitbit API and Google Sheets API."""

from pathlib import Path

from config import Config
from oauth import auth_flow


def google_auth(creds_path: Path) -> None:
    print()
    print("Google")
    print("------")
    auth_flow(
        creds_path=creds_path,
        scope=["https://www.googleapis.com/auth/drive.readonly"],
        auth_url="https://accounts.google.com/o/oauth2/auth",
        token_url="https://oauth2.googleapis.com/token",
    )


def fitbit_auth(creds_path: Path) -> None:
    print()
    print("Fitbit")
    print("------")
    auth_flow(
        creds_path=creds_path,
        scope=["oxygen_saturation"],
        auth_url="https://www.fitbit.com/oauth2/authorize",
        token_url="https://api.fitbit.com/oauth2/token",
    )


def main() -> None:
    config = Config()
    try:
        fitbit_auth(config.fitbit_creds)
        google_auth(config.google_creds)
        # TODO: Other APIs
        print("\nSuccess!")
    except KeyboardInterrupt:
        print("\nCanceled")
        exit(1)
    except Exception as ex:
        print(f"Failed: {ex}")
        exit(1)


if __name__ == "__main__":
    main()
