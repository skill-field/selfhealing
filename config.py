"""Configuration for Skillfield Sentinel."""

import logging
import os
import sys

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    CDSW_APP_PORT: int = 8081
    IS_CML: bool = False

    # API Keys
    ANTHROPIC_API_KEY: str = ""
    GITHUB_TOKEN: str = ""

    # AWS Bedrock (default LLM provider)
    AWS_REGION: str = "ap-southeast-2"
    USE_BEDROCK: bool = True  # Uses AWS Bedrock for Claude calls

    # GitHub
    GITHUB_REPO: str = "koshaji/metrics"

    # Application
    METRICS_APP_URL: str = "https://m8x.ai"
    SENTINEL_SECRET: str = ""
    SENTINEL_API_KEY: str = ""  # API key for endpoint auth (empty = no auth)
    LOG_POLL_INTERVAL: int = 60

    # Database
    DB_PATH: str = "data/sentinel.db"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def model_post_init(self, __context) -> None:
        """Detect if running in CML environment."""
        if os.environ.get("CDSW_APP_PORT"):
            self.IS_CML = True


settings = Settings()


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_level = logging.DEBUG if not settings.IS_CML else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Quiet down noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
