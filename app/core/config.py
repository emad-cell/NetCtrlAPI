from pydantic_settings import BaseSettings ,SettingsConfigDict

class Settings(BaseSettings):
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = ""
    ENCRYPTION_KEY: str | None = None

    GNS3_HOST: str = "localhost"
    GNS3_PORT: int = 3080
    GNS3_USER: str = ""
    GNS3_PASS: str = ""

    API_KEY: str = ""

    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8001

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env"
    )

# Single instance imported everywhere
settings = Settings()
