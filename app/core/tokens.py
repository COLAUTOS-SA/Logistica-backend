"""
Generador de tokens de acceso directo (magic links).
Cada token es un UUID válido 72 horas, de uso único.
La URL resultante apunta al frontend: APP_URL/acceso/<token>
"""
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import dotenv_values

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"


def _app_url() -> str:
    cfg = dotenv_values(_env_path)
    return cfg.get("APP_URL", "http://localhost:5173").rstrip("/")


def generar_url_acceso(db, email: str, redirigir_a: str = "/reclamaciones") -> str:
    """
    Crea un token de acceso directo para `email` y retorna la URL completa.
    Si falla (error de DB), retorna "" para que el correo se envíe sin botón.
    """
    from app.models.tokens import AccesoDirecto
    try:
        token = str(uuid.uuid4())
        db.add(AccesoDirecto(
            token=token,
            email=email,
            redirigir_a=redirigir_a,
            expira_en=datetime.utcnow() + timedelta(hours=72),
        ))
        db.commit()
        return f"{_app_url()}/acceso/{token}"
    except Exception as e:
        db.rollback()
        print(f"[TOKEN] No se pudo crear token para {email}: {e}")
        return ""
