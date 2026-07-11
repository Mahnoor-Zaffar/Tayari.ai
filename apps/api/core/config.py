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

    OPENAI_API_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    RESEND_API_KEY: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

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
