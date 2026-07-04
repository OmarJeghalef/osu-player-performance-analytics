"""Transform raw osu! API JSON files into clean analysis-ready datasets."""

from pathlib import Path
from typing import Any
import json

import pandas as pd

# Constants for file paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Finds the newest raw JSON file for a given dataset prefix and loads it into a dictionary.
def get_latest_raw_file(dataset_prefix: str) -> Path:
    """
    Find the newest raw JSON file for a given dataset prefix.

    Example:
        dataset_prefix='user_profile'
        matches files like user_profile_mrekk_osu_2026-07-04_163012.json
    """

    matching_files = sorted(
        RAW_DATA_DIR.glob(f"{dataset_prefix}_*.json"),
        key=lambda file_path: file_path.stat().st_mtime,
        reverse=True,
    )

    if not matching_files:
        raise FileNotFoundError(
            f"No raw files found for prefix {dataset_prefix!r} in {RAW_DATA_DIR}"
        )

    return matching_files[0]

# Load one raw JSON file from disk.
def load_raw_json(file_path: Path) -> dict[str, Any]:
    """Load one raw JSON file from disk."""

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)

# Turns one raw osu! user profile response into a flat one-row DataFrame.
def build_player_profile_snapshot(raw_payload: dict[str, Any]) -> pd.DataFrame:
    """
    Convert one raw osu! user profile response into a flat one-row DataFrame.

    The raw payload has this structure:
        {
            "metadata": {...},
            "data": {...}
        }

    The processed output keeps only fields that are useful for analysis.
    """

    metadata = raw_payload.get("metadata") or {}
    user = raw_payload.get("data") or {}

    statistics = user.get("statistics") or {}
    country = user.get("country") or {}
    level = statistics.get("level") or {}

    row = {
        "extracted_at_utc": metadata.get("extracted_at_utc"),
        "source": metadata.get("source"),
        "mode": metadata.get("mode"),

        "user_id": user.get("id"),
        "username": user.get("username"),
        "country_code": user.get("country_code"),
        "country_name": country.get("name"),

        "global_rank": statistics.get("global_rank"),
        "country_rank": statistics.get("country_rank"),
        "pp": statistics.get("pp"),
        "hit_accuracy": statistics.get("hit_accuracy"),
        "play_count": statistics.get("play_count"),
        "play_time": statistics.get("play_time"),
        "total_score": statistics.get("total_score"),
        "ranked_score": statistics.get("ranked_score"),
        "maximum_combo": statistics.get("maximum_combo"),
        "replays_watched": statistics.get("replays_watched_by_others"),

        "level_current": level.get("current"),
        "level_progress": level.get("progress"),
    }

    return pd.DataFrame([row])

# Cleans up the DataFrame by converting types and ordering columns.
def clean_player_profile_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Apply basic type cleanup and column ordering."""

    integer_columns = [
        "user_id",
        "global_rank",
        "country_rank",
        "play_count",
        "play_time",
        "total_score",
        "ranked_score",
        "maximum_combo",
        "replays_watched",
        "level_current",
        "level_progress",
    ]

    float_columns = [
        "pp",
        "hit_accuracy",
    ]

    for column in integer_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    for column in float_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["extracted_at_utc"] = pd.to_datetime(df["extracted_at_utc"], errors="coerce")

    ordered_columns = [
        "extracted_at_utc",
        "source",
        "mode",
        "user_id",
        "username",
        "country_code",
        "country_name",
        "global_rank",
        "country_rank",
        "pp",
        "hit_accuracy",
        "play_count",
        "play_time",
        "total_score",
        "ranked_score",
        "maximum_combo",
        "replays_watched",
        "level_current",
        "level_progress",
    ]

    return df[ordered_columns]

# Saves a processed DataFrame as a CSV file.
def save_processed_csv(df: pd.DataFrame, dataset_name: str) -> Path:
    """Save a processed DataFrame as a CSV file."""

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DATA_DIR / f"{dataset_name}.csv"
    df.to_csv(output_path, index=False)

    return output_path

# Main function to orchestrate the transformation process
def main() -> None:
    """Transform the latest raw user profile JSON into a processed CSV."""

    try:
        latest_raw_file = get_latest_raw_file("user_profile")
        raw_payload = load_raw_json(latest_raw_file)

        player_profile_df = build_player_profile_snapshot(raw_payload)
        player_profile_df = clean_player_profile_snapshot(player_profile_df)

        output_path = save_processed_csv(
            df=player_profile_df,
            dataset_name="player_profile_snapshot",
        )

        print(f"Loaded raw file: {latest_raw_file}")
        print(f"Saved processed file: {output_path}")
        print()
        print("Processed player profile snapshot:")
        print(player_profile_df.to_string(index=False))

    except (FileNotFoundError, KeyError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()