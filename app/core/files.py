"""Almacenamiento local o en NAS de los archivos adjuntos."""

import os
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


BASE_ARCHIVOS = Path(settings.FILE_STORAGE_ROOT).expanduser().resolve()

ARCHIVO_CATEGORIAS = {
    "foto": "fotos",
    "video": "videos",
    "soporte": "soportes",
    "cotizacion": "cotizaciones",
    "factura": "facturas",
    "certificado": "certificados",
}
DOCUMENTO_TIPOS = {
    "manifiesto": "manifiestos",
    "remesa": "remesas",
    "inventario": "inventarios",
    "inventario_traslado": "inventarios_traslado",
}
EXTENSIONES_PERMITIDAS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".webp", ".heic",
    ".mp4", ".mov", ".avi", ".mkv",
    ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt",
}


def _error_archivo(mensaje: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mensaje)


def _componente_seguro(valor: str, campo: str) -> str:
    """Crea un componente de ruta legible sin permitir separadores ni traversal."""
    normalizado = unicodedata.normalize("NFKD", (valor or "")).encode("ascii", "ignore").decode()
    resultado = re.sub(r"[^A-Za-z0-9._-]+", "-", normalizado).strip(".-_")
    if not resultado or resultado in {".", ".."}:
        _error_archivo(f"{campo} no tiene un valor válido para almacenar el archivo")
    return resultado[:120]


def _nombre_archivo_seguro(nombre_original: str) -> str:
    nombre = Path(nombre_original or "").name
    base, extension = os.path.splitext(nombre)
    extension = extension.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        _error_archivo("Tipo de archivo no permitido")
    return f"{_componente_seguro(base, 'El nombre del archivo')[:180]}{extension}"


def _guardar_en_carpeta(archivo: UploadFile, carpeta: Path) -> str:
    """Copia en bloques, limita el tamaño y elimina copias incompletas si algo falla."""
    nombre = _nombre_archivo_seguro(archivo.filename or "")
    destino = carpeta / nombre
    limite_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    escritos = 0
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        if destino.exists():
            base, extension = os.path.splitext(nombre)
            destino = carpeta / f"{base}_{datetime.now():%Y%m%d%H%M%S}_{uuid4().hex[:8]}{extension}"
        with destino.open("xb") as salida:
            while bloque := archivo.file.read(1024 * 1024):
                escritos += len(bloque)
                if escritos > limite_bytes:
                    _error_archivo(f"El archivo supera el límite de {settings.MAX_UPLOAD_MB} MB")
                salida.write(bloque)
    except HTTPException:
        if destino.exists():
            destino.unlink(missing_ok=True)
        raise
    except OSError as exc:
        if destino.exists():
            destino.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible guardar el archivo. Verifique la disponibilidad de la NAS.",
        ) from exc
    finally:
        archivo.file.seek(0)

    return destino.name


def guardar_archivo(archivo: UploadFile, ano: str, mes: str, rec_id: str, categoria: str) -> str:
    """Guarda reclamaciones en reclamaciones/AAAA/MM/REC-ID/categoria/."""
    if categoria not in ARCHIVO_CATEGORIAS:
        _error_archivo("Categoría de archivo no válida")
    carpeta = BASE_ARCHIVOS / "reclamaciones" / _componente_seguro(ano, "Año") / _componente_seguro(mes, "Mes")
    carpeta /= _componente_seguro(rec_id, "Identificador de reclamación") / ARCHIVO_CATEGORIAS[categoria]
    nombre = _guardar_en_carpeta(archivo, carpeta)
    return (Path("reclamaciones") / ano / mes / _componente_seguro(rec_id, "Identificador de reclamación") / ARCHIVO_CATEGORIAS[categoria] / nombre).as_posix()


def guardar_documento(archivo: UploadFile, tipo: str, numero: str, fecha: str | None = None) -> str:
    """Guarda documentos por tipo, año y número de documento."""
    if tipo not in DOCUMENTO_TIPOS:
        _error_archivo("Tipo de documento no válido")
    try:
        ano = datetime.strptime(fecha, "%Y-%m-%d").strftime("%Y") if fecha else datetime.now().strftime("%Y")
    except ValueError:
        _error_archivo("La fecha del documento debe tener el formato YYYY-MM-DD")
    carpeta = BASE_ARCHIVOS / "documentos" / DOCUMENTO_TIPOS[tipo] / ano / _componente_seguro(numero, "Número de documento")
    nombre = _guardar_en_carpeta(archivo, carpeta)
    return (Path("documentos") / DOCUMENTO_TIPOS[tipo] / ano / _componente_seguro(numero, "Número de documento") / nombre).as_posix()


def dias_habiles_transcurridos(fecha_inicio: datetime) -> int:
    """Calcula días hábiles (lunes-viernes) entre fecha_inicio y hoy."""
    hoy = date.today()
    inicio = fecha_inicio.date() if isinstance(fecha_inicio, datetime) else fecha_inicio
    count = 0
    current = inicio
    while current <= hoy:
        if current.weekday() < 5:
            count += 1
        current = date.fromordinal(current.toordinal() + 1)
    return count
