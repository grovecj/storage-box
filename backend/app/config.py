from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://storagebox:changeme@db:5432/storagebox"
    app_base_url: str = "http://localhost"
    app_env: str = "development"
    secret_key: str = "dev-secret-key"
    db_ca_cert: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 7 days

    model_config = {"env_file": ".env"}


settings = Settings()
