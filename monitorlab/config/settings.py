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

    # Vision Model Configuration (Qwen2-VL-4B)
    vision_api_base: str = Field(
        default="http://localhost:1234/v1", alias="VISION_API_BASE"
    )
    vision_model: str = Field(default="Qwen2-VL-4B-Instruct", alias="VISION_MODEL")
    vision_temperature: float = Field(default=0.2, alias="VISION_TEMPERATURE")
    vision_max_tokens: int = Field(default=1000, alias="VISION_MAX_TOKENS")

    # MCP Configuration
    mcp_playwright_enabled: bool = Field(default=True, alias="MCP_PLAYWRIGHT_ENABLED")
    mcp_playwright_server: str = Field(default="stdio", alias="MCP_PLAYWRIGHT_SERVER")

    # Agent Configuration
    max_concurrent_agents: int = Field(default=5, alias="MAX_CONCURRENT_AGENTS")
    agent_timeout: int = Field(default=300, alias="AGENT_TIMEOUT")  # seconds
    max_retries: int = Field(default=3, alias="MAX_RETRIES")

    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./monitorlab.db", alias="DATABASE_URL"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default="monitorlab.log", alias="LOG_FILE")

    # Screenshots
    screenshot_dir: str = Field(default="./screenshots", alias="SCREENSHOT_DIR")
    screenshot_quality: int = Field(default=90, alias="SCREENSHOT_QUALITY")

    # Gradio Configuration
    gradio_server_port: int = Field(default=7860, alias="GRADIO_SERVER_PORT")
    gradio_share: bool = Field(default=False, alias="GRADIO_SHARE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
