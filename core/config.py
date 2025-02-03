from pydantic_settings import BaseSettings,SettingsConfigDict
from functools import lru_cache
from pathlib import Path



class Settings(BaseSettings):
    APP_NAME: str = "Task Manager"
    DEBUG: bool = False
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path(__file__).parent.parent}/tasks.db"
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

        
@lru_cache
def get_settings() -> Settings:
    return Settings()