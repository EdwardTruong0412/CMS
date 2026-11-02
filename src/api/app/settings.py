from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CMS_", env_file=None, case_sensitive=False, extra="ignore"
    )

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cms"
    db_user: str = "cms"
    db_password: SecretStr
    db_sslmode: Literal["disable", "prefer", "require", "verify-ca", "verify-full"] = "require"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
