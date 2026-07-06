"""Load validated processed osu! datasets into PostgreSQL."""

from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Define paths to processed data files and environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

PROFILE_CSV = PROCESSED_DATA_DIR / "player_profile_snapshot.csv"
BEST_SCORES_CSV = PROCESSED_DATA_DIR / "player_best_scores.csv"

# Load environment variables from .env file
def get_database_url() -> str:
    """Load the PostgreSQL database URL from the local .env file."""

    load_dotenv(ENV_FILE)

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is missing from .env")

    return database_url

# Read a processed CSV file into a DataFrame, ensuring the file exists.
def read_processed_csv(file_path: Path) -> pd.DataFrame:
    """Read one processed CSV file."""

    if not file_path.exists():
        raise FileNotFoundError(f"Processed CSV not found: {file_path}")

    return pd.read_csv(file_path)

# Prepare the DataFrame for loading into PostgreSQL by converting columns to appropriate types.
def prepare_profile_for_load(df: pd.DataFrame) -> pd.DataFrame:
    """Convert profile CSV columns to database-friendly types."""

    df = df.copy()

    datetime_columns = [
        "extracted_at_utc",
    ]

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

    for column in datetime_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce", utc=True)

    for column in integer_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    for column in float_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df

# Prepare the DataFrame for loading into PostgreSQL by converting columns to appropriate types.
def prepare_best_scores_for_load(df: pd.DataFrame) -> pd.DataFrame:
    """Convert best-score CSV columns to database-friendly types."""

    df = df.copy()

    datetime_columns = [
        "extracted_at_utc",
        "created_at",
        "beatmapset_ranked_date",
    ]

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

    for column in datetime_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce", utc=True)

    for column in integer_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    for column in float_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in boolean_columns:
        df[column] = df[column].astype("boolean")

    return df

# Delete existing best-score rows before inserting the latest CSV to prevent primary-key conflicts.
def delete_existing_best_scores(connection, score_ids: list[int]) -> None:
    """
    Delete existing best-score rows before inserting the latest CSV.

    This prevents primary-key conflicts if the same score_id is loaded more than once.
    """

    if not score_ids:
        return

    connection.execute(
        text("DELETE FROM player_best_scores WHERE score_id = ANY(:score_ids)"),
        {"score_ids": score_ids},
    )

# Load processed player profile snapshot rows into PostgreSQL.
def load_player_profile_snapshot(connection, profile_df: pd.DataFrame) -> None:
    """Append player profile snapshot rows to PostgreSQL."""

    profile_df.to_sql(
        "player_profile_snapshots",
        con=connection,
        if_exists="append",
        index=False,
    )

# Load processed player best scores rows into PostgreSQL.
def load_player_best_scores(connection, best_scores_df: pd.DataFrame) -> None:
    """Insert player best scores into PostgreSQL."""

    score_ids = (
        pd.to_numeric(best_scores_df["score_id"], errors="coerce")
        .dropna()
        .astype(int)
        .tolist()
    )

    delete_existing_best_scores(connection, score_ids)

    best_scores_df.to_sql(
        "player_best_scores",
        con=connection,
        if_exists="append",
        index=False,
    )

# Print row counts from loaded PostgreSQL tables.
def print_table_counts(connection) -> None:
    """Print row counts from loaded PostgreSQL tables."""

    profile_count = connection.execute(
        text("SELECT COUNT(*) FROM player_profile_snapshots")
    ).scalar_one()

    best_scores_count = connection.execute(
        text("SELECT COUNT(*) FROM player_best_scores")
    ).scalar_one()

    print("PostgreSQL load complete")
    print(f"player_profile_snapshots rows: {profile_count}")
    print(f"player_best_scores rows: {best_scores_count}")

# Main function to orchestrate the loading process
def main() -> None:
    """Load processed CSV files into PostgreSQL tables."""

    try:
        database_url = get_database_url()

        profile_df = prepare_profile_for_load(read_processed_csv(PROFILE_CSV))
        best_scores_df = prepare_best_scores_for_load(read_processed_csv(BEST_SCORES_CSV))

        engine = create_engine(database_url)

        with engine.begin() as connection:
            load_player_profile_snapshot(connection, profile_df)
            load_player_best_scores(connection, best_scores_df)
            print_table_counts(connection)

    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()
