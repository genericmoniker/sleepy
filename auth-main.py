"""Configure authentication for the Fitbit API and Google Sheets API."""

import json
from pathlib import Path

from oauth import authorize, fetch_token
from config import Config


def fitbit_auth(creds_path: Path) -> None:
    print("Fitbit")
    print("------")
    client_id = input("Enter your Fitbit client ID: ")
    client_secret = input("Enter your Fitbit client secret: ")
    redirect_uri = "http://localhost:8000"
    scope = ["oxygen_saturation"]
    auth_url = "https://www.fitbit.com/oauth2/authorize"
    try:
        response, state = authorize(
            auth_url=auth_url,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            redirect_uri=redirect_uri,
        )
        token_response = fetch_token(
            token_url="https://api.fitbit.com/oauth2/token",
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            auth_response=response,
            state=state,
        )
        creds = {
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token": token_response["access_token"],
            "refresh_token": token_response["refresh_token"],
        }
        with creds_path.open("w") as creds_file:
            creds_file.write(json.dumps(creds))
        print("Fitbit authentication successful!")
    except Exception as ex:
        print(f"Fitbit authentication failed: {ex}")
        exit(1)


def main() -> None:
    config = Config()
    try:
        fitbit_auth(config.fitbit_creds)
        # TODO: Other APIs
    except KeyboardInterrupt:
        print("\nAuthentication canceled.")
        exit(1)


if __name__ == "__main__":
    main()
