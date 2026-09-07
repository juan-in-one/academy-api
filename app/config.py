from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración vía variables de entorno (ver .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://academy_api:academy_api@localhost:5434/academy_api"
    app_name: str = "academy-api"


settings = Settings()
