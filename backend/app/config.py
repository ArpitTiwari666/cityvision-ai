from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://cityvision:cityvision@db:5432/cityvision"
    cors_origins: str = "http://localhost:5173"
    demo_mode: bool = True
    jwt_secret: str = "replace-in-production"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
