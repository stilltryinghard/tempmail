from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # POSTGRES
    postgres_host: str
    postgres_port: int = 5432
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str

    # REDIS
    redis_host: str
    redis_port: int = 6379

    # SERVICE
    mail_domain: str
    mailbox_ttl_minutes: int = 10
    brevo_webhook_secret: SecretStr
    rate_limit_per_minute: int = 5
    debug: bool = False


settings = Settings()
