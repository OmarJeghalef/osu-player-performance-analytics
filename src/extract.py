"""Extract public player data from the osu! API v2 and save raw JSON files."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from config import Settings

# Constants for osu! API endpoints and request settings
TOKEN_URL = "https://osu.ppy.sh/oauth/token"
API_BASE_URL = "https://osu.ppy.sh/api/v2"
REQUEST_TIMEOUT_SECONDS = 30

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


class OsuApiError(RuntimeError):
    """Raised when an osu! API request fails."""

# Get an OAuth access token using the Client Credentials Grant, which allows access to public osu! API data.
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

# Send an authorized GET request to the osu! API.
def make_authorized_get_request(
    access_token: str,
    url: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Send one authorized GET request to the osu! API and return the JSON response."""

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response else "unknown"
        raise OsuApiError(f"osu! API returned HTTP {status_code} for {url}") from error
    except requests.RequestException as error:
        raise OsuApiError(f"Failed to connect to the osu! API: {error}") from error

    return response.json()

# Retrieve one osu! player's public profile and statistics.
def get_user(
    access_token: str,
    username: str,
    mode: str = "osu",
) -> dict[str, Any]:
    """Retrieve one osu! player's public profile and statistics."""

    encoded_username = quote(f"@{username}", safe="")
    url = f"{API_BASE_URL}/users/{encoded_username}/{mode}"

    user = make_authorized_get_request(access_token=access_token, url=url)

    if not isinstance(user, dict):
        raise OsuApiError("Expected user profile response to be a JSON object.")

    return user

# Retrieve a player's best scores from the osu! API.
def get_user_best_scores(
    access_token: str,
    user_id: int,
    mode: str = "osu",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Retrieve a player's best scores.

    The osu! API supports score types such as best, firsts, and recent.
    For this analytics project, best scores are the most useful starting point.
    """

    if limit < 1 or limit > 100:
        raise ValueError("Best score limit must be between 1 and 100.")

    url = f"{API_BASE_URL}/users/{user_id}/scores/best"
    params = {
        "mode": mode,
        "limit": limit,
    }

    scores = make_authorized_get_request(
        access_token=access_token,
        url=url,
        params=params,
    )

    if not isinstance(scores, list):
        raise OsuApiError("Expected best scores response to be a JSON array.")

    return scores

#  Build a consistent raw data filename based on dataset name, username, mode, and timestamp.
def build_raw_filename(
    dataset_name: str,
    username: str,
    mode: str,
    timestamp: datetime,
) -> str:
    """Build a consistent raw data filename."""

    formatted_timestamp = timestamp.strftime("%Y-%m-%d_%H%M%S")
    safe_username = username.lower().replace(" ", "_")

    return f"{dataset_name}_{safe_username}_{mode}_{formatted_timestamp}.json"

# Save raw API data as a timestamped JSON file.
def save_raw_json(
    data: Any,
    dataset_name: str,
    username: str,
    mode: str,
) -> Path:
    """Save raw API data as a timestamped JSON file."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    extraction_time = datetime.now(timezone.utc)
    filename = build_raw_filename(
        dataset_name=dataset_name,
        username=username,
        mode=mode,
        timestamp=extraction_time,
    )

    output_path = RAW_DATA_DIR / filename

    payload = {
        "metadata": {
            "dataset_name": dataset_name,
            "username": username,
            "mode": mode,
            "extracted_at_utc": extraction_time.isoformat(),
            "source": "osu_api_v2",
        },
        "data": data,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    return output_path

# Print a small validation summary of the retrieved user profile without exposing credentials.
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

# Print a small summary of the retrieved best scores without exposing credentials.
def print_best_scores_summary(scores: list[dict[str, Any]]) -> None:
    """Print a small summary of extracted best scores."""

    print()
    print(f"Best scores retrieved: {len(scores)}")

    if not scores:
        print("No best scores returned.")
        return

    top_score = scores[0]
    beatmap = top_score.get("beatmap") or {}
    beatmapset = top_score.get("beatmapset") or {}

    print("Top score preview:")
    print(f"Score ID: {top_score.get('id')}")
    print(f"PP: {top_score.get('pp')}")
    print(f"Accuracy: {top_score.get('accuracy')}")
    print(f"Rank: {top_score.get('rank')}")
    print(f"Beatmapset: {beatmapset.get('artist')} - {beatmapset.get('title')}")
    print(f"Difficulty: {beatmap.get('version')}")

# Main function to orchestrate the extraction process
def main() -> None:
    """Load settings, retrieve player data, and save raw JSON files."""

    try:
        settings = Settings.from_environment()
        access_token = get_access_token(settings)

        user = get_user(
            access_token=access_token,
            username=settings.osu_username,
            mode=settings.osu_mode,
        )

        user_id = user.get("id")

        if not isinstance(user_id, int):
            raise OsuApiError("User profile response did not contain a valid integer id.")

        best_scores = get_user_best_scores(
            access_token=access_token,
            user_id=user_id,
            mode=settings.osu_mode,
            limit=100,
        )

        profile_output_path = save_raw_json(
            data=user,
            dataset_name="user_profile",
            username=settings.osu_username,
            mode=settings.osu_mode,
        )

        best_scores_output_path = save_raw_json(
            data=best_scores,
            dataset_name="user_best_scores",
            username=settings.osu_username,
            mode=settings.osu_mode,
        )

        print_user_summary(user)
        print_best_scores_summary(best_scores)
        print()
        print(f"Raw profile JSON saved to: {profile_output_path}")
        print(f"Raw best scores JSON saved to: {best_scores_output_path}")

    except (ValueError, OsuApiError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()