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
    llm_allow_rule_based_fallback: bool = False
    openai_api_key: str | None = None
    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "data"
    )
    agent_runtime: Literal["legacy", "react"] = "react"
    agent_max_steps: int = 20
    agent_max_tool_calls: int = 30
    agent_action_parse_retries: int = 2
    agent_enable_repair: bool = True
    agent_enable_trace: bool = True
    agent_max_repair_attempts: int = 2
    agent_max_revision_attempts: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def effective_llm_api_key(self) -> str | None:
        return self.llm_api_key or self.openai_api_key

    @property
    def resolved_data_dir(self) -> Path:
        if self.data_dir.is_absolute():
            return self.data_dir

        backend_root = Path(__file__).resolve().parents[3]
        package_data_dir = Path(__file__).resolve().parents[1] / "data"
        candidates = [
            Path.cwd() / self.data_dir,
            backend_root / self.data_dir,
            package_data_dir,
        ]
        unique_candidates = list(dict.fromkeys(candidates))
        for candidate in unique_candidates:
            if _looks_like_data_dir(candidate):
                return candidate
        for candidate in unique_candidates:
            if candidate.exists():
                return candidate
        return unique_candidates[0]


def _looks_like_data_dir(path: Path) -> bool:
    return any(
        (path / filename).exists()
        for filename in (
            "poi.json",
            "poi.sample.json",
            "route_edges.json",
            "route_edges.sample.json",
        )
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
