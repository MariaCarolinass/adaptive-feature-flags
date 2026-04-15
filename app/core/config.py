from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Feature Flags API"
    database_url: str = "sqlite:///./db.sqlite3"
    environment: str = "development"
    log_level: str = "INFO"
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    cors_allowed_origins: list[str] = ["http://localhost", "http://127.0.0.1", "http://localhost:3000"]
    enable_docs: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_json_loads=True,
    )


settings = Settings()
