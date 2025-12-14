from functools import lru_cache
from typing import List

from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    app_name: str = "ICS Forensics Platform"
    debug: bool = False
    database_url: str = "sqlite:///./ics_platform.db"
    api_prefix: str = "/api"
    allowed_hosts: List[str] = ["*"]
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    report_dir: str = "./reports"

    class Config:
        env_prefix = "ICS_"
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
