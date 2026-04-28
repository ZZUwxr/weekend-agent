from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Weekend Agent"
    app_env: str = "local"
    llm_provider: Literal["mock", "openai"] = "mock"
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 60
    llm_max_retries: int = 2
    llm_temperature: float = 0.2
    llm_use_structured_output: bool = True
    llm_api_style: Literal["chat_completions", "responses"] = "chat_completions"
    llm_trust_env: bool = False
    openai_api_key: str | None = None
    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "data"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def effective_llm_api_key(self) -> str | None:
        return self.llm_api_key or self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
