from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.database import engine, Base
from app.core.files import BASE_ARCHIVOS
from app.core.scheduler import scheduler
import app.models  # registra todos los modelos con SQLAlchemy

from app.routers import auth, claims, users, documents

# Crear todas las tablas si no existen (incluye notificaciones_enviadas)
Base.metadata.create_all(bind=engine)

# Asegurarse de que la carpeta de archivos existe
os.makedirs(BASE_ARCHIVOS, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranca el scheduler al iniciar y lo detiene al apagar."""
    scheduler.start()
    print("[SCHEDULER] Iniciado – alertas de vencimiento a las 7:00 AM (Bogotá)")
    yield
    scheduler.shutdown(wait=False)
    print("[SCHEDULER] Detenido")


app = FastAPI(
    title="COLAUTOS – API de Gestión Logística",
    version="2.0.0",
    description="Backend para el sistema de reclamaciones a transportadoras de Col Autos.",
    lifespan=lifespan,
)

# CORS – permite que el frontend en localhost:5173 se conecte sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (fotos, videos, PDFs, etc.)
# Accesibles en: http://localhost:8000/archivos/2026/06/REC-2026-001/foto.jpg
app.mount("/archivos", StaticFiles(directory=BASE_ARCHIVOS), name="archivos")

# Registrar todos los routers
app.include_router(auth.router)
app.include_router(claims.router)
app.include_router(users.router)
app.include_router(documents.router)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "sistema": "COLAUTOS Gestión Logística",
        "version": "2.0.0"
    }


@app.post("/admin/enviar-alertas", tags=["Admin"])
def enviar_alertas_manual():
    """Dispara manualmente el chequeo de vencimientos (para pruebas)."""
    from app.core.scheduler import verificar_vencimientos
    verificar_vencimientos()
    return {"ok": True, "mensaje": "Verificación de vencimientos ejecutada"}
