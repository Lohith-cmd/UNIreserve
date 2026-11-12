from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_DB: str = "unireserve"
    POSTGRES_USER: str = "unireserve"
    POSTGRES_PASSWORD: str = "unireserve"
    DATABASE_URL: str = "postgresql://unireserve:unireserve@localhost:5432/unireserve"
    
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY_PATH: str = "./backend/keys/private.pem"
    JWT_PUBLIC_KEY_PATH: str = "./backend/keys/public.pem"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        extra="ignore"
    )


settings = Settings()

