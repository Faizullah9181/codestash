from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CodeStash API"
    env: str = "development"
    database_url: str = "postgresql+asyncpg://codestash:codestash@localhost:5432/codestash"
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
