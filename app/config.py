from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auctions"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FIREBASE_CREDENTIALS_PATH: str | None = None
    FIREBASE_PROJECT_ID: str | None = None

    SOFT_CLOSE_WINDOW_MINUTES: int = 5
    SOFT_CLOSE_EXTENSION_MINUTES: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
