from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ERICA_", extra="ignore")

    skills_path: Path = _repo_root() / "skills"
    config_path: Path = _repo_root() / "config"
    data_path: Path = _repo_root() / "data"
    windows_cli: str | None = None
    agent_host: str = "127.0.0.1"
    agent_port: int = 8742

    # LLM planning (OpenAI-compatible Chat Completions). Set LLM_API_KEY to enable.
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"


settings = Settings()
