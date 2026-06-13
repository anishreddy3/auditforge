"""Configuration loader for AuditForge."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration from environment variables."""

    # Terminal 3
    TERMINAL3_API_KEY: str = os.getenv("TERMINAL3_API_KEY", "")

    # Bright Data
    BRIGHTDATA_API_KEY: str = os.getenv("BRIGHTDATA_API_KEY", "")
    BRIGHTDATA_ZONE: str = os.getenv("BRIGHTDATA_ZONE", "")

    # Kimi K2.6
    KIMI_API_KEY: str = os.getenv("KIMI_API_KEY", "")
    KIMI_BASE_URL: str = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")

    # Daytona
    DAYTONA_API_KEY: str = os.getenv("DAYTONA_API_KEY", "")
    DAYTONA_BASE_URL: str = os.getenv("DAYTONA_BASE_URL", "")

    # TokenRouter
    TOKENROUTER_API_KEY: str = os.getenv("TOKENROUTER_API_KEY", "")
    TOKENROUTER_BASE_URL: str = os.getenv("TOKENROUTER_BASE_URL", "")


config = Config()
