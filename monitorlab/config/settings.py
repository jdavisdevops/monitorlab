"""Configuration settings for MonitorLab."""

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    llm_api_base: str = Field(default="http://localhost:1234/v1", alias="LLM_API_BASE")
    llm_api_key: str = Field(default="not-needed", alias="LLM_API_KEY")
    llm_model: str = Field(default="local-model", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, alias="LLM_MAX_TOKENS")

    # Vision Model Configuration
    vision_api_base: str = Field(
        default="http://localhost:1234/v1", alias="VISION_API_BASE"
    )
    vision_model: str = Field(default="local-vision-model", alias="VISION_MODEL")
    vision_temperature: float = Field(default=0.3, alias="VISION_TEMPERATURE")
    vision_max_tokens: int = Field(default=1000, alias="VISION_MAX_TOKENS")

    # Browser Configuration
    headless: bool = Field(default=False, alias="HEADLESS")
    browser_timeout: int = Field(default=30000, alias="BROWSER_TIMEOUT")
    default_viewport_width: int = Field(default=1920, alias="DEFAULT_VIEWPORT_WIDTH")
    default_viewport_height: int = Field(default=1080, alias="DEFAULT_VIEWPORT_HEIGHT")
    slow_mo: int = Field(default=0, alias="SLOW_MO")  # Milliseconds to slow down operations

    # Agent Configuration
    max_concurrent_agents: int = Field(default=3, alias="MAX_CONCURRENT_AGENTS")
    agent_timeout: int = Field(default=300, alias="AGENT_TIMEOUT")  # seconds
    max_retries: int = Field(default=3, alias="MAX_RETRIES")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default="monitorlab.log", alias="LOG_FILE")

    # Screenshots
    screenshot_dir: str = Field(default="./screenshots", alias="SCREENSHOT_DIR")
    screenshot_quality: int = Field(default=90, alias="SCREENSHOT_QUALITY")
    screenshot_full_page: bool = Field(default=True, alias="SCREENSHOT_FULL_PAGE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
