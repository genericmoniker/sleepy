"""Data from the Fitbit API.

A note on "creds" parameters:

The dict is expected to have these keys:
    - client_id
    - client_secret
    - authorization_code

It may also have these keys, and they may be updated during function calls:
    - access_token
    - refresh_token

https://dev.fitbit.com/build/reference/web-api/
"""

from base64 import b64encode
from datetime import datetime

import httpx


# The timeout for requests to the Fitbit API. The API can sometimes be slow to respond,
# perhaps due to request throttling.
REQUEST_TIMEOUT = 30


class CredentialsError(Exception):
    """Credentials are invalid (e.g. empty or expired)."""


def get_spo2(creds: dict, begin: datetime, end: datetime | None = None) -> list[dict]:
    """Get intra-day SpO2 data for a date range.

    From the API documentation:

    This endpoint returns the SpO2 intraday data for a specified date range. SpO2
    applies specifically to a user’s “main sleep”, which is the longest single period of
    time asleep on a given date. Spo2 values are calculated on a 5-minute
    exponentially-moving average.

    The measurement is provided at the end of a period of sleep. The data returned
    usually reflects a sleep period that began the day before. For example, if you
    request SpO2 levels for 2021-12-22, it may include measurements that were taken the
    previous night on 2021-12-21 when the user fell asleep.

    The data returned includes the percentage value of SpO2 in your bloodstream and an
    accurate timestamp for that measurement.

    Example:

    {'dateTime': '2024-10-06', 'minutes': [{...}, {...}, {...}, {...}, {...}, {...},
    {...}, {...}, {...}, {...}, {...}, {...}, {...}, {...}, {...}, {...}, {...}, {...},
    {...}, ...]}

    {'value': 98.6, 'minute': '2024-10-05T23:03:34'}
    """
    end = end or datetime.now()
    begin_str = begin.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    url_path = f"spo2/date/{begin_str}/{end_str}/all.json"
    return _api_request(creds, url_path)


def _api_request(creds: dict, url_path: str) -> list[dict]:
    """Make a request to the Fitbit API.

    If the request fails due to an expired access token, the token is refreshed, the
    creds dict is updated and the request is retried.
    """
    if not creds:
        raise CredentialsError
    access_token = creds.get("access_token", "")
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        url = "https://api.fitbit.com/1/user/-/" + url_path
        try:
            return _do_resource_get(client, access_token, url)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 401:  # noqa: PLR2004
                try:
                    access_token = _refresh_access_token(client, creds)
                    return _do_resource_get(client, access_token, url)
                except httpx.HTTPStatusError as ex:
                    raise CredentialsError(ex.response.json()) from ex
            raise


def get_access_token(
    client: httpx.Client,
    authorization_code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> tuple[str, str]:
    """Exchange an authorization code for an access token and refresh token.

    The return value is a tuple of (access_token, refresh_token).

    https://dev.fitbit.com/build/reference/web-api/oauth2/#access_token-request
    """
    post_data = {
        "code": authorization_code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    data = _do_auth_post(client, client_id, client_secret, post_data)
    return data["access_token"], data["refresh_token"]


def _refresh_access_token(client: httpx.Client, creds: dict) -> str:
    """Exchange a refresh token for a new access token and refresh token.

    The creds dict is updated with the new tokens, and the new access token is
    also returned.

    https://dev.fitbit.com/build/reference/web-api/oauth2/#refreshing-tokens
    """
    post_data = {
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    }
    data = _do_auth_post(
        client,
        creds["client_id"],
        creds["client_secret"],
        post_data,
    )
    creds["access_token"] = data["access_token"]
    creds["refresh_token"] = data["refresh_token"]
    return data["access_token"]


def _do_resource_get(
    client: httpx.Client,
    access_token: str,
    url: str,
) -> list[dict]:
    """Make a GET request to the resource server."""
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def _do_auth_post(
    client: httpx.Client,
    client_id: str,
    client_secret: str,
    post_data: dict,
) -> dict:
    """Make a POST request to the authorization server."""
    url = "https://api.fitbit.com/oauth2/token"
    auth_value = b64encode(f"{client_id}:{client_secret}".encode())
    headers = {"Authorization": "Basic " + auth_value.decode()}
    response = client.post(url, headers=headers, data=post_data)
    response.raise_for_status()
    return response.json()
