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

    @property
    def is_production(self) -> bool:
        """True when running in the production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """True for local development and the test suite."""
        return self.ENVIRONMENT in ("development", "test")

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
    FRONTEND_URL: str = "http://localhost:3000"

    # Public base URL of this API as seen by browsers (used to build the CSP
    # connect-src for HTTP + WebSocket).  Override in production, e.g.
    # https://api.tayari.ai
    PUBLIC_API_URL: str = "http://localhost:8000"

    AI_INTERVIEWER_MODEL: str = "openai/gpt-4o-mini"
    AI_EVALUATOR_MODEL: str = "openai/gpt-4o-mini"

    # Model gateway routing. Empty model overrides mean "use the task default"
    # (AI_INTERVIEWER_MODEL for chat, AI_EVALUATOR_MODEL for structured output).
    MODEL_GATEWAY_CHAT_MODEL: str = ""
    MODEL_GATEWAY_STRUCTURED_MODEL: str = ""

    # Observability — per-call AI usage telemetry persisted to the ai_usage table.
    AI_USAGE_ENABLED: bool = True
    AI_USAGE_FLUSH_INTERVAL_S: int = 15
    AI_MAX_TOKENS_PER_INTERVIEW: int = 10000
    AI_COST_CAP_DOLLARS: float = 0.30

    INTERVIEW_DURATION_MINUTES: int = 30
    GRACE_PERIOD_MINUTES: int = 10

    STORAGE_BUCKET: str = "tayari-evaluations"
    STORAGE_ENDPOINT: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_REGION: str = "us-east-1"

    DEEPGRAM_API_KEY: str = ""
    DEEPGRAM_MODEL: str = "nova-3"
    DEEPGRAM_ENDPOINTING: int = 300  # ms of silence before finalizing speech

    SENTRY_DSN: str = ""

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Comma-separated list of email addresses that are granted admin role
    # on registration.  Falls back to "admin@tayari.ai" when unset.
    ADMIN_EMAILS: str = "admin@tayari.ai"


settings = Settings()
