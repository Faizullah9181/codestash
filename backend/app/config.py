from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CodeStash API"
    env: str = "development"
    api_docs_enabled: bool = False
    database_url: str = "postgresql+asyncpg://codestash:codestash@localhost:5432/codestash"
    cors_origins: str = "http://localhost:5173"


settings = Settings()
