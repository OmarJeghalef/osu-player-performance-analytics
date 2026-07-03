"""Extract public player data from the osu! API v2."""

from typing import Any
from urllib.parse import quote

import requests

from config import Settings

# Constants for osu! API endpoints and request timeout
TOKEN_URL = "https://osu.ppy.sh/oauth/token"
API_BASE_URL = "https://osu.ppy.sh/api/v2"
REQUEST_TIMEOUT_SECONDS = 30


class OsuApiError(RuntimeError):
    """Raised when an osu! API request fails."""

# Get the access token using the Client Credentials Grant
def get_access_token(settings: Settings) -> str:
    """
    Request an OAuth access token using the Client Credentials Grant.

    The resulting token allows this project to access public osu! API data.
    """

    payload = {
        "client_id": settings.osu_client_id,
        "client_secret": settings.osu_client_secret,
        "grant_type": "client_credentials",
        "scope": "public",
    }

    try:
        response = requests.post(
            TOKEN_URL,
            data=payload,
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise OsuApiError(f"Failed to obtain osu! API access token: {error}") from error

    token_data = response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise OsuApiError("The token response did not contain an access_token.")

    return access_token

# Retrieve one osu! player's public profile and statistics
def get_user(
    access_token: str,
    username: str,
    mode: str = "osu",
) -> dict[str, Any]:
    """Retrieve one osu! player's public profile and statistics."""

    encoded_username = quote(f"@{username}", safe="")
    url = f"{API_BASE_URL}/users/{encoded_username}/{mode}"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response else "unknown"

        if status_code == 404:
            raise OsuApiError(
                f"osu! user {username!r} was not found in mode {mode!r}."
            ) from error

        raise OsuApiError(
            f"osu! API returned HTTP {status_code} while retrieving the user."
        ) from error
    except requests.RequestException as error:
        raise OsuApiError(f"Failed to connect to the osu! API: {error}") from error

    return response.json()

# Print a small validation summary without exposing credentials
def print_user_summary(user: dict[str, Any]) -> None:
    """Print a small validation summary without exposing credentials."""

    statistics = user.get("statistics") or {}
    country = user.get("country") or {}

    print("osu! API connection successful")
    print(f"Username: {user.get('username')}")
    print(f"User ID: {user.get('id')}")
    print(f"Country: {country.get('name')}")
    print(f"Global rank: {statistics.get('global_rank')}")
    print(f"Country rank: {statistics.get('country_rank')}")
    print(f"Performance points: {statistics.get('pp')}")
    print(f"Accuracy: {statistics.get('hit_accuracy')}")
    print(f"Play count: {statistics.get('play_count')}")

# Main function to load settings, authenticate, and retrieve the configured player
def main() -> None:
    """Load settings, authenticate, and retrieve the configured player."""

    try:
        settings = Settings.from_environment()
        access_token = get_access_token(settings)
        user = get_user(
            access_token=access_token,
            username=settings.osu_username,
            mode=settings.osu_mode,
        )
        print_user_summary(user)
    except (ValueError, OsuApiError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()