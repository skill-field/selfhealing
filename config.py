"""Configuration for Skillfield Sentinel."""

import os
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

    # AWS Bedrock (use instead of ANTHROPIC_API_KEY)
    AWS_REGION: str = "us-east-1"
    USE_BEDROCK: bool = False  # Set to true to use AWS Bedrock instead of Anthropic API

    # GitHub
    GITHUB_REPO: str = "koshaji/metrics"

    # Application
    METRICS_APP_URL: str = "https://m8x.ai"
    SENTINEL_SECRET: str = ""
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
