import os

from urllib.parse import quote_plus

from dotenv import load_dotenv

from pydantic_settings import BaseSettings


# Cargar variables del archivo .env
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

    PROJECT_NAME: str = os.getenv(
        "PROJECT_NAME",
        "COLAUTOS Logistica"
    )

    DATABASE_URL: str = _build_db_url()

    # SendGrid
    SENDGRID_API_KEY: str = os.getenv(
        "SENDGRID_API_KEY",
        ""
    )

    EMAIL_FROM: str = os.getenv(
        "EMAIL_FROM",
        ""
    )

    # CORS
    ALLOWED_HOSTS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://logistica.colautos.co",
        "http://logistica.colautos.co",
    ]


settings = Settings()