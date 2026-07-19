from datetime import timedelta

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "Tayari AI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://tayari:tayari_dev@localhost:5432/tayari"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "RS256"  # Use RS256 in prod, HS256 for dev simplicity
    JWT_EXPIRY_HOURS: int = 24
    JWT_REFRESH_EXPIRY_DAYS: int = 7
    JWT_EMAIL_VERIFY_EXPIRY_HOURS: int = 24
    JWT_PASSWORD_RESET_EXPIRY_HOURS: int = 1

    @computed_field
    @property
    def jwt_access_token_ttl(self) -> timedelta:
        return timedelta(hours=self.JWT_EXPIRY_HOURS)

    @computed_field
    @property
    def jwt_refresh_token_ttl(self) -> timedelta:
        return timedelta(days=self.JWT_REFRESH_EXPIRY_DAYS)

    @computed_field
    @property
    def jwt_email_verify_ttl(self) -> timedelta:
        return timedelta(hours=self.JWT_EMAIL_VERIFY_EXPIRY_HOURS)

    @computed_field
    @property
    def jwt_password_reset_ttl(self) -> timedelta:
        return timedelta(hours=self.JWT_PASSWORD_RESET_EXPIRY_HOURS)

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    RESEND_API_KEY: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3030", "http://localhost:3001"]

    AI_INTERVIEWER_MODEL: str = "gpt-4o-mini"
    AI_EVALUATOR_MODEL: str = "gpt-4o"
    AI_MAX_TOKENS_PER_INTERVIEW: int = 10000
    AI_COST_CAP_DOLLARS: float = 0.30

    INTERVIEW_DURATION_MINUTES: int = 30
    GRACE_PERIOD_MINUTES: int = 10

    STORAGE_BUCKET: str = "tayari-evaluations"
    STORAGE_ENDPOINT: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""


settings = Settings()
