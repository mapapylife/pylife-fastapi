from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    db_url: str = "sqlite:///db.sqlite3"
    redis_url: str = "redis://localhost:6379/"
    auth_token: Optional[str] = None

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
