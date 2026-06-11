from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_token: str
    capashino_base_url: str
    database_url: str
    kafka_bootstrap_servers: str

    class Config:
        env_file = ".env"


settings = Settings()
