"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

# Load environment variables from .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

# Define the Settings dataclass to hold configuration values
@dataclass(frozen=True)
class Settings:
    """Configuration required to access the osu! API."""

    osu_client_id: int
    osu_client_secret: str
    osu_username: str
    osu_mode: str = "osu"
    
    @classmethod
    def from_environment(cls) -> "Settings":
        """Create validated settings from environment variables."""

        client_id = os.getenv("OSU_CLIENT_ID")
        client_secret = os.getenv("OSU_CLIENT_SECRET")
        username = os.getenv("OSU_USERNAME")
        mode = os.getenv("OSU_MODE", "osu").lower()

        missing_variables = [
            variable_name
            for variable_name, value in {
                "OSU_CLIENT_ID": client_id,
                "OSU_CLIENT_SECRET": client_secret,
                "OSU_USERNAME": username,
            }.items()
            if not value
        ]

        if missing_variables:
            missing = ", ".join(missing_variables)
            raise ValueError(
                f"Missing required environment variables: {missing}. "
                "Create a .env file based on .env.example."
            )

        assert client_id is not None and client_secret is not None and username is not None

        try:
            parsed_client_id = int(client_id)
        except ValueError as error:
            raise ValueError("OSU_CLIENT_ID must be an integer.") from error

        valid_modes = {"osu", "taiko", "fruits", "mania"}

        if mode not in valid_modes:
            raise ValueError(
                f"OSU_MODE must be one of {sorted(valid_modes)}; received {mode!r}."
            )

        return cls(
            osu_client_id=parsed_client_id,
            osu_client_secret=client_secret,
            osu_username=username,
            osu_mode=mode,
        )