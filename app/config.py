from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    lms_api_key: str = Field(alias="LMS_API_KEY")
    postgres_connection_string: str = Field(alias="POSTGRES_CONNECTION_STRING")
    kafka_bootstrap_servers: str = Field(alias="KAFKA_BOOTSTRAP_SERVERS")
    capashino_base_url: str = Field(alias="CAPASHINO_BASE_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def async_database_url(self) -> str:
        """Для FastAPI: заменяем postgres:// на postgresql+asyncpg://"""
        url = self.postgres_connection_string
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Для Alembic: заменяем postgres:// на postgresql://"""
        url = self.postgres_connection_string
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
