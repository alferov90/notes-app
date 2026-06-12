from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://notes:notes@localhost:5432/notes"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""

    @field_validator("telegram_bot_token", "telegram_bot_username", mode="before")
    @classmethod
    def strip_value(cls, v: str) -> str:
        if not v:
            return ""
        return str(v).strip()

    @field_validator("telegram_bot_username", mode="after")
    @classmethod
    def strip_at_sign(cls, v: str) -> str:
        return v.lstrip("@") if v else v


settings = Settings()
