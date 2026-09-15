from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import dotenv_values
from pathlib import Path
import os

_env = dotenv_values(Path(__file__).resolve().parent.parent / ".env")
_ADMIN_KEY = _env.get("ADMIN_API_KEY", "")


def _require_admin_key(x_admin_key: str = Header(default="")):
    """Verifica que el header X-Admin-Key coincida con ADMIN_API_KEY del .env."""
    if not _ADMIN_KEY:
        return  # Si no está configurada, no se bloquea (desarrollo local)
    if x_admin_key != _ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Clave de administrador inválida")

from app.core.database import engine, Base
from app.core.files import BASE_ARCHIVOS
from app.core.scheduler import scheduler
import app.models  # registra todos los modelos con SQLAlchemy

from app.routers import auth, claims, users, documents

# Crear todas las tablas si no existen (incluye notificaciones_enviadas)
Base.metadata.create_all(bind=engine)

# Migraciones manuales: agregar columnas nuevas si no existen
def _migrar():
    with engine.connect() as conn:
        # documentos.observacion
        try:
            conn.execute(__import__('sqlalchemy').text("ALTER TABLE documentos ADD COLUMN observacion TEXT"))
            conn.commit()
            print("[DB] Columna 'observacion' agregada a documentos")
        except Exception:
            pass  # ya existe

_migrar()

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

# CORS – orígenes leídos del .env (ALLOWED_ORIGINS) con fallback a localhost para desarrollo
_cors_env = _env.get("ALLOWED_ORIGINS", "")
_cors_origins = (
    [o.strip() for o in _cors_env.split(",") if o.strip()]
    if _cors_env else
    ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://localhost:3000"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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
def enviar_alertas_manual(correo_prueba: str = None, x_admin_key: str = Header(default="")):
    """Dispara manualmente el chequeo de vencimientos.
    Si se pasa ?correo_prueba=tu@email.com, el correo va solo a ese destino."""
    _require_admin_key(x_admin_key)
    from app.core.scheduler import verificar_vencimientos
    verificar_vencimientos(correo_prueba=correo_prueba)
    return {"ok": True, "mensaje": "Verificación de vencimientos ejecutada"}


@app.post("/admin/enviar-nueva-reclamacion-prueba", tags=["Admin"])
def enviar_nueva_reclamacion_prueba(correo_prueba: str = None, x_admin_key: str = Header(default="")):
    """Envía un correo de prueba de 'nueva reclamación' al correo indicado."""
    from app.core.email import enviar_correo_nueva_reclamacion
    from datetime import datetime
    destinatarios = [correo_prueba] if correo_prueba else []
    if not destinatarios:
        return {"ok": False, "mensaje": "Pasa ?correo_prueba=tu@email.com"}
    _require_admin_key(x_admin_key)
    enviar_correo_nueva_reclamacion(destinatarios, {
        "id":            "REC-2026-TEST",
        "vin":           "3MDDJ2HAAVM461828",
        "vehiculo":      "Mazda CX-30 2026 - Machine Gray",
        "tipo_novedad":  "Desconche",
        "descripcion":   "Desconche en la nave trasera del vehículo. Se detectó al momento de la recepción en bodega Pereira.",
        "transportadora": "BERGE Vigía",
        "no_remesa":     "VIG-2100790",
        "no_manifiesto": "410900097200",
        "sede":          "Pereira - Av 30 de Agosto",
        "reportado_por": "Lorena Gómez",
        "fecha_reporte": datetime.now(),
    })
    return {"ok": True, "mensaje": f"Correo de prueba enviado a {correo_prueba}"}


@app.post("/admin/enviar-colision-prueba", tags=["Admin"])
def enviar_colision_prueba(correo_prueba: str = None, x_admin_key: str = Header(default="")):
    """Envía un correo de prueba de 'novedad asignada a colisión' con datos ficticios."""
    from app.core.email import enviar_correo_colision
    from datetime import datetime
    destinatarios = [correo_prueba] if correo_prueba else []
    if not destinatarios:
        return {"ok": False, "mensaje": "Pasa ?correo_prueba=tu@email.com"}
    _require_admin_key(x_admin_key)
    enviar_correo_colision(destinatarios, {
        "id":            "REC-2026-TEST",
        "vin":           "3MDDJ2HAAVM461828",
        "vehiculo":      "Mazda CX-30 2026 - Machine Gray",
        "tipo_novedad":  "Desconche",
        "descripcion":   "Desconche en la nave trasera del vehículo. Se detectó al momento de la recepción en bodega Pereira.",
        "transportadora": "BERGE Vigía",
        "no_remesa":     "VIG-2100790",
        "no_manifiesto": "410900097200",
        "sede":          "Pereira - Av 30 de Agosto",
        "reportado_por": "Lorena Gómez",
        "fecha_reporte": datetime.now(),
    })
    return {"ok": True, "mensaje": f"Correo de colisión enviado a {correo_prueba}"}


@app.post("/admin/enviar-alertas-prueba", tags=["Admin"])
def enviar_alertas_vencimiento_prueba(correo_prueba: str = None, x_admin_key: str = Header(default="")):
    """Envía un correo de prueba de alertas de vencimiento con datos ficticios."""
    from app.core.email import enviar_correo_vencimientos
    destinatarios = [correo_prueba] if correo_prueba else []
    if not destinatarios:
        return {"ok": False, "mensaje": "Pasa ?correo_prueba=tu@email.com"}
    alertas = [
        {
            "id":             "REC-2026-042",
            "vin":            "3MDDJ2HAAVM461828",
            "vehiculo":       "Mazda CX-30 2026 - Machine Gray",
            "transportadora": "BERGE Vigía",
            "dias_habiles":   9,
            "dias_limite":    10,
            "responsable":    "Lorena Gómez",
        },
        {
            "id":             "REC-2026-038",
            "vin":            "9BWZZZ377VT004251",
            "vehiculo":       "Mazda 3 Sedan 2025 - Soul Red",
            "transportadora": "Mobility",
            "dias_habiles":   8,
            "dias_limite":    10,
            "responsable":    "Carlos Pérez",
        },
    ]
    vencidas = [
        {
            "id":             "REC-2026-031",
            "vin":            "1HGBH41JXMN109186",
            "vehiculo":       "Mazda CX-5 2026 - Polymetal Gray",
            "transportadora": "Transportes Especiales",
            "dias_habiles":   13,
            "dias_limite":    10,
            "responsable":    "Ana Martínez",
        },
    ]
    _require_admin_key(x_admin_key)
    enviar_correo_vencimientos(destinatarios, alertas, vencidas)
    return {"ok": True, "mensaje": f"Correo de prueba de alertas enviado a {correo_prueba}"}
