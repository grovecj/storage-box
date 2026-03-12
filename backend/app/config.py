from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://storagebox:changeme@db:5432/storagebox"
    app_base_url: str = "http://localhost"
    app_env: str = "development"
    secret_key: str = "dev-secret-key"
    db_ca_cert_path: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
