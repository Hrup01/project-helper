from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    database_url: str = "sqlite:///./data/project_helper.db"
    repos_dir: str = "./data/repos"
    max_file_bytes: int = 120_000
    max_analyzed_files: int = 180

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def data_dir(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", "")).parent
        return Path("./data")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    Path(settings.repos_dir).mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
