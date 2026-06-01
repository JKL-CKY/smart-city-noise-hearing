from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./noise_hearing.db"
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"

    OPENAI_API_KEY: str = ""
    WHISPER_MODEL: str = "base"
    PYANNOTE_AUTH_TOKEN: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    ENVIRONMENT_DEPARTMENT_EMAIL: str = "env@city.gov"
    URBAN_PLANNING_EMAIL: str = "planning@city.gov"

    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
