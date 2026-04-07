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


settings = Settings()
