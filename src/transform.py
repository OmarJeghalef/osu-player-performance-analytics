"""Transform raw osu! API JSON files into clean analysis-ready datasets."""

from pathlib import Path
from typing import Any
import json

import pandas as pd

# Constants for project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Get the latest raw JSON file for a given dataset prefix.
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

# Load one raw JSON file.
def load_raw_json(file_path: Path) -> dict[str, Any]:
    """Load one raw JSON file from disk."""

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)

# Build a player profile snapshot DataFrame from raw JSON data.
def build_player_profile_snapshot(raw_payload: dict[str, Any]) -> pd.DataFrame:
    """
    Convert one raw osu! user profile response into a flat one-row DataFrame.
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

# Clean up the player profile snapshot DataFrame by applying type conversions and ordering columns.
def clean_player_profile_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Apply basic type cleanup and column ordering to the profile snapshot."""

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

# Build a player best scores DataFrame from raw JSON data.
def build_player_best_scores(raw_payload: dict[str, Any]) -> pd.DataFrame:
    """
    Convert raw osu! best score data into a flat score-level DataFrame.

    Each score becomes one row.
    """

    metadata = raw_payload.get("metadata") or {}
    scores = raw_payload.get("data") or []

    rows: list[dict[str, Any]] = []

    for score_index, score in enumerate(scores, start=1):
        beatmap = score.get("beatmap") or {}
        beatmapset = score.get("beatmapset") or {}
        weight = score.get("weight") or {}
        statistics = score.get("statistics") or {}

        raw_mods = score.get("mods") or []

        if all(isinstance(mod, dict) for mod in raw_mods):
            mod_acronyms = [
                mod.get("acronym")
                for mod in raw_mods
                if mod.get("acronym")
            ]
        else:
            mod_acronyms = [str(mod) for mod in raw_mods]

        beatmap_id = score.get("beatmap_id") or beatmap.get("id")
        beatmapset_id = beatmap.get("beatmapset_id") or beatmapset.get("id")

        user_id = score.get("user_id")
        if user_id is None:
            user = score.get("user") or {}
            user_id = user.get("id")

        row = {
            "extracted_at_utc": metadata.get("extracted_at_utc"),
            "source": metadata.get("source"),
            "mode": metadata.get("mode"),
            "username": metadata.get("username"),

            "top_play_rank": score_index,
            "score_id": score.get("id"),
            "user_id": user_id,
            "beatmap_id": beatmap_id,
            "beatmapset_id": beatmapset_id,

            "score": score.get("score"),
            "pp": score.get("pp"),
            "accuracy": score.get("accuracy"),
            "rank": score.get("rank"),
            "max_combo": score.get("max_combo"),
            "passed": score.get("passed"),
            "perfect": score.get("perfect"),
            "created_at": score.get("created_at"),

            "mods": ",".join(mod_acronyms),
            "ruleset_id": score.get("mode_int") if score.get("mode_int") is not None else beatmap.get("mode_int"),

            "count_300": statistics.get("count_300"),
            "count_100": statistics.get("count_100"),
            "count_50": statistics.get("count_50"),
            "count_miss": statistics.get("count_miss"),

            "weight_percentage": weight.get("percentage"),
            "weight_pp": weight.get("pp"),

            "beatmap_difficulty_name": beatmap.get("version"),
            "beatmap_total_length": beatmap.get("total_length"),
            "beatmap_hit_length": beatmap.get("hit_length"),
            "beatmap_bpm": beatmap.get("bpm"),
            "beatmap_cs": beatmap.get("cs"),
            "beatmap_ar": beatmap.get("ar"),
            "beatmap_od": beatmap.get("accuracy"),
            "beatmap_hp": beatmap.get("drain"),
            "beatmap_star_rating": beatmap.get("difficulty_rating"),
            "beatmap_status": beatmap.get("status"),

            "beatmapset_artist": beatmapset.get("artist"),
            "beatmapset_title": beatmapset.get("title"),
            "beatmapset_creator": beatmapset.get("creator"),
            "beatmapset_ranked_date": beatmapset.get("ranked_date"),
        }

        rows.append(row)

    return pd.DataFrame(rows)

# Clean up the player best scores DataFrame by applying type conversions and ordering columns.
def clean_player_best_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Apply basic type cleanup and column ordering to best scores."""

    if df.empty:
        return df

    integer_columns = [
        "top_play_rank",
        "score_id",
        "user_id",
        "beatmap_id",
        "beatmapset_id",
        "score",
        "max_combo",
        "ruleset_id",
        "count_300",
        "count_100",
        "count_50",
        "count_miss",
        "beatmap_total_length",
        "beatmap_hit_length",
    ]

    float_columns = [
        "pp",
        "accuracy",
        "weight_percentage",
        "weight_pp",
        "beatmap_bpm",
        "beatmap_cs",
        "beatmap_ar",
        "beatmap_od",
        "beatmap_hp",
        "beatmap_star_rating",
    ]

    boolean_columns = [
        "passed",
        "perfect",
    ]

    datetime_columns = [
        "extracted_at_utc",
        "created_at",
        "beatmapset_ranked_date",
    ]

    for column in integer_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    for column in float_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in boolean_columns:
        df[column] = df[column].astype("boolean")

    for column in datetime_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    ordered_columns = [
        "extracted_at_utc",
        "source",
        "mode",
        "username",
        "top_play_rank",
        "score_id",
        "user_id",
        "beatmap_id",
        "beatmapset_id",
        "score",
        "pp",
        "accuracy",
        "rank",
        "max_combo",
        "passed",
        "perfect",
        "created_at",
        "mods",
        "ruleset_id",
        "count_300",
        "count_100",
        "count_50",
        "count_miss",
        "weight_percentage",
        "weight_pp",
        "beatmap_difficulty_name",
        "beatmap_total_length",
        "beatmap_hit_length",
        "beatmap_bpm",
        "beatmap_cs",
        "beatmap_ar",
        "beatmap_od",
        "beatmap_hp",
        "beatmap_star_rating",
        "beatmap_status",
        "beatmapset_artist",
        "beatmapset_title",
        "beatmapset_creator",
        "beatmapset_ranked_date",
    ]

    return df[ordered_columns]

# Save a processed DataFrame as a CSV file.
def save_processed_csv(df: pd.DataFrame, dataset_name: str) -> Path:
    """Save a processed DataFrame as a CSV file."""

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DATA_DIR / f"{dataset_name}.csv"
    df.to_csv(output_path, index=False)

    return output_path

# Transform the latest raw user profile JSON into a processed CSV.
def transform_player_profile() -> Path:
    """Transform the latest raw user profile JSON into a processed CSV."""

    latest_raw_file = get_latest_raw_file("user_profile")
    raw_payload = load_raw_json(latest_raw_file)

    player_profile_df = build_player_profile_snapshot(raw_payload)
    player_profile_df = clean_player_profile_snapshot(player_profile_df)

    output_path = save_processed_csv(
        df=player_profile_df,
        dataset_name="player_profile_snapshot",
    )

    print(f"Loaded raw profile file: {latest_raw_file}")
    print(f"Saved processed profile file: {output_path}")
    print()
    print("Processed player profile snapshot:")
    print(player_profile_df.to_string(index=False))
    print()

    return output_path

# Transform the latest raw best scores JSON into a processed CSV.
def transform_player_best_scores() -> Path:
    """Transform the latest raw best scores JSON into a processed CSV."""

    latest_raw_file = get_latest_raw_file("user_best_scores")
    raw_payload = load_raw_json(latest_raw_file)

    best_scores_df = build_player_best_scores(raw_payload)
    best_scores_df = clean_player_best_scores(best_scores_df)

    output_path = save_processed_csv(
        df=best_scores_df,
        dataset_name="player_best_scores",
    )

    print(f"Loaded raw best scores file: {latest_raw_file}")
    print(f"Saved processed best scores file: {output_path}")
    print()
    print("Processed best scores preview:")
    preview_columns = [
        "top_play_rank",
        "pp",
        "accuracy",
        "rank",
        "mods",
        "beatmap_star_rating",
        "beatmapset_artist",
        "beatmapset_title",
        "beatmap_difficulty_name",
        "created_at",
    ]
    print(best_scores_df[preview_columns].head(10).to_string(index=False))
    print()

    return output_path

# Main function to orchestrate the transformation process
def main() -> None:
    """Transform the latest raw osu! API files into processed CSV datasets."""

    try:
        transform_player_profile()
        transform_player_best_scores()

    except (FileNotFoundError, KeyError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()