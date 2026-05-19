"""Application settings loaded from environment variables."""

from __future__ import annotations

from cryptography.fernet import Fernet
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from `.env` (see `.env.example`)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: SecretStr
    telegram_webhook_secret: SecretStr | None = None

    # LLM
    anthropic_api_key: SecretStr
    default_llm_model: str = "claude-haiku-4-5-20251001"
    analysis_llm_model: str = "claude-sonnet-4-6"

    # Supabase
    supabase_url: str
    supabase_service_key: SecretStr

    # Security
    telegram_id_hash_salt: SecretStr
    encryption_key: SecretStr

    # Observability
    sentry_dsn: str = ""
    log_level: str = "INFO"

    # App
    app_env: str = "development"
    app_port: int = 8000
    use_polling: bool = True

    @field_validator("encryption_key")
    @classmethod
    def _validate_fernet_key(cls, v: SecretStr) -> SecretStr:
        """Reject startup if ENCRYPTION_KEY isn't a valid Fernet key."""
        try:
            Fernet(v.get_secret_value().encode())
        except (ValueError, TypeError) as e:
            raise ValueError(
                "ENCRYPTION_KEY is not a valid Fernet key. Generate one with: "
                "python -c 'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())'"
            ) from e
        return v


def get_settings() -> Settings:
    """Return a Settings instance. Fails loudly if a required env var is missing."""
    return Settings()  # type: ignore[call-arg]
