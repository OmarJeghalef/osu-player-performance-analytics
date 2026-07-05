"""Validate processed osu! analytics datasets before database loading."""

from pathlib import Path

import pandas as pd

# Define paths to processed data files
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

PROFILE_CSV = PROCESSED_DATA_DIR / "player_profile_snapshot.csv"
BEST_SCORES_CSV = PROCESSED_DATA_DIR / "player_best_scores.csv"


class DataValidationError(ValueError):
    """Raised when a processed dataset fails validation."""

# Validate that a required file exists, and raise an error if it does not.
def require_file_exists(file_path: Path) -> None:
    """Validate that a required file exists."""

    if not file_path.exists():
        raise DataValidationError(f"Required file does not exist: {file_path}")

# Validate that a DataFrame contains required columns.
def require_columns(df: pd.DataFrame, required_columns: list[str], dataset_name: str) -> None:
    """Validate that a DataFrame contains required columns."""

    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        raise DataValidationError(
            f"{dataset_name} is missing required columns: {missing_columns}"
        )

# Validate that a DataFrame has at least one row.
def require_non_empty(df: pd.DataFrame, dataset_name: str) -> None:
    """Validate that a DataFrame has at least one row."""

    if df.empty:
        raise DataValidationError(f"{dataset_name} has no rows.")

# Validate that selected columns do not contain null values.
def require_no_nulls(
    df: pd.DataFrame,
    columns: list[str],
    dataset_name: str,
) -> None:
    """Validate that selected columns do not contain null values."""

    null_counts = df[columns].isna().sum()
    failing_columns = null_counts[null_counts > 0]

    if not failing_columns.empty:
        raise DataValidationError(
            f"{dataset_name} has null values in required columns: "
            f"{failing_columns.to_dict()}"
        )

# Validate that a column contains unique values.
def require_unique(df: pd.DataFrame, column: str, dataset_name: str) -> None:
    """Validate that a column contains unique values."""

    duplicate_count = df[column].duplicated().sum()

    if duplicate_count > 0:
        raise DataValidationError(
            f"{dataset_name} has {duplicate_count} duplicate values in {column!r}."
        )

# Validate that a numeric column falls within an expected range.
def require_numeric_range(
    df: pd.DataFrame,
    column: str,
    dataset_name: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> None:
    """Validate that a numeric column falls within an expected range."""

    values = pd.to_numeric(df[column], errors="coerce")

    if values.isna().any():
        raise DataValidationError(
            f"{dataset_name}.{column} contains non-numeric or missing values."
        )

    if minimum is not None and (values < minimum).any():
        bad_count = int((values < minimum).sum())
        raise DataValidationError(
            f"{dataset_name}.{column} has {bad_count} values below {minimum}."
        )

    if maximum is not None and (values > maximum).any():
        bad_count = int((values > maximum).sum())
        raise DataValidationError(
            f"{dataset_name}.{column} has {bad_count} values above {maximum}."
        )

# Validate that a column can be parsed as datetimes.
def require_datetime_parseable(
    df: pd.DataFrame,
    column: str,
    dataset_name: str,
) -> None:
    """Validate that a column can be parsed as datetimes."""

    parsed_values = pd.to_datetime(df[column], errors="coerce", utc=True)

    if parsed_values.isna().any():
        bad_count = int(parsed_values.isna().sum())
        raise DataValidationError(
            f"{dataset_name}.{column} has {bad_count} unparseable datetime values."
        )

# Validate the processed player profile snapshot dataset.
def validate_player_profile_snapshot() -> None:
    """Validate the processed player profile snapshot dataset."""

    dataset_name = "player_profile_snapshot"

    require_file_exists(PROFILE_CSV)

    df = pd.read_csv(PROFILE_CSV)

    required_columns = [
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
    ]

    require_non_empty(df, dataset_name)
    require_columns(df, required_columns, dataset_name)

    if len(df) != 1:
        raise DataValidationError(
            f"{dataset_name} should contain exactly 1 row, found {len(df)}."
        )

    require_no_nulls(
        df,
        [
            "extracted_at_utc",
            "user_id",
            "username",
            "mode",
            "pp",
            "hit_accuracy",
            "play_count",
        ],
        dataset_name,
    )

    require_numeric_range(df, "user_id", dataset_name, minimum=1)
    require_numeric_range(df, "pp", dataset_name, minimum=0)
    require_numeric_range(df, "hit_accuracy", dataset_name, minimum=0, maximum=100)
    require_numeric_range(df, "play_count", dataset_name, minimum=0)
    require_datetime_parseable(df, "extracted_at_utc", dataset_name)

    print(f"Validated {dataset_name}: {len(df)} row")

# Validate the processed player best scores dataset.
def validate_player_best_scores() -> None:
    """Validate the processed player best scores dataset."""

    dataset_name = "player_best_scores"

    require_file_exists(BEST_SCORES_CSV)

    df = pd.read_csv(BEST_SCORES_CSV)

    required_columns = [
        "extracted_at_utc",
        "mode",
        "username",
        "top_play_rank",
        "score_id",
        "user_id",
        "beatmap_id",
        "score",
        "pp",
        "accuracy",
        "rank",
        "max_combo",
        "created_at",
        "beatmap_star_rating",
        "beatmapset_artist",
        "beatmapset_title",
        "beatmap_difficulty_name",
    ]

    require_non_empty(df, dataset_name)
    require_columns(df, required_columns, dataset_name)

    require_no_nulls(
        df,
        [
            "extracted_at_utc",
            "top_play_rank",
            "score_id",
            "user_id",
            "beatmap_id",
            "pp",
            "accuracy",
            "rank",
            "created_at",
        ],
        dataset_name,
    )

    require_unique(df, "score_id", dataset_name)

    require_numeric_range(df, "top_play_rank", dataset_name, minimum=1, maximum=100)
    require_numeric_range(df, "score_id", dataset_name, minimum=1)
    require_numeric_range(df, "user_id", dataset_name, minimum=1)
    require_numeric_range(df, "beatmap_id", dataset_name, minimum=1)
    require_numeric_range(df, "score", dataset_name, minimum=0)
    require_numeric_range(df, "pp", dataset_name, minimum=0)
    require_numeric_range(df, "accuracy", dataset_name, minimum=0, maximum=1)
    require_numeric_range(df, "max_combo", dataset_name, minimum=0)
    require_numeric_range(df, "beatmap_star_rating", dataset_name, minimum=0)

    require_datetime_parseable(df, "extracted_at_utc", dataset_name)
    require_datetime_parseable(df, "created_at", dataset_name)

    expected_ranks = set(range(1, len(df) + 1))
    actual_ranks = set(pd.to_numeric(df["top_play_rank"], errors="coerce").dropna().astype(int))

    if actual_ranks != expected_ranks:
        raise DataValidationError(
            f"{dataset_name}.top_play_rank should contain sequential values "
            f"from 1 to {len(df)}."
        )

    print(f"Validated {dataset_name}: {len(df)} rows")

# Main function to orchestrate the validation process
def main() -> None:
    """Run all processed data validation checks."""

    try:
        validate_player_profile_snapshot()
        validate_player_best_scores()
        print()
        print("All validation checks passed.")

    except DataValidationError as error:
        raise SystemExit(f"Validation failed: {error}") from error


if __name__ == "__main__":
    main()
