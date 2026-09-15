import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(override=True)

def _build_db_url() -> str:
    host = os.getenv("DB_HOST", "")
    if not host:
        return "sqlite:///./colautos.db"
    user = os.getenv("DB_USER", "")
    password = quote_plus(os.getenv("DB_PASS", ""))
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "COLAUTOS Logistica")
    DATABASE_URL: str = _build_db_url()
    FILE_STORAGE_ROOT: str = os.getenv(
        "FILE_STORAGE_ROOT",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "archivos_reclamaciones"),
    )
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "100"))
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://logistica.colautos.co/api")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    DB_POOL_RECYCLE_SECONDS: int = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "300"))
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "5"))
    ALLOWED_HOSTS: list = ["http://localhost:3000", "http://localhost:5173", "https://logistica.colautos.co", "http://logistica.colautos.co"]

settings = Settings()
