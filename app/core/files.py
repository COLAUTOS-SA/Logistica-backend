import os
import shutil
from datetime import date, datetime
from fastapi import UploadFile

# Ruta base donde se guardan todos los archivos de reclamaciones
BASE_ARCHIVOS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "archivos_reclamaciones")
BASE_DOCUMENTOS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "documentos")


def guardar_archivo(archivo: UploadFile, año: str, mes: str, rec_id: str) -> str:
    """
    Guarda el archivo en: archivos_reclamaciones/{año}/{mes}/{rec_id}/{nombre}
    Devuelve la ruta RELATIVA desde BASE_ARCHIVOS para guardar en DB.
    """
    carpeta = os.path.join(BASE_ARCHIVOS, año, mes, rec_id)
    os.makedirs(carpeta, exist_ok=True)

    # Evitar colisiones de nombre
    nombre = archivo.filename
    ruta_completa = os.path.join(carpeta, nombre)
    if os.path.exists(ruta_completa):
        ts = datetime.now().strftime("%H%M%S")
        base, ext = os.path.splitext(nombre)
        nombre = f"{base}_{ts}{ext}"
        ruta_completa = os.path.join(carpeta, nombre)

    with open(ruta_completa, "wb") as dest:
        shutil.copyfileobj(archivo.file, dest)

    # Ruta relativa (la que se monta en /archivos)
    return os.path.join(año, mes, rec_id, nombre)


def guardar_documento(archivo: UploadFile, tipo: str, numero: str) -> str:
    """
    Guarda documentos en: documentos/{tipo}/{numero}/{nombre}
    Devuelve la ruta relativa dentro de BASE_ARCHIVOS para servir por HTTP.
    """
    # Los documentos los servimos también desde archivos/documentos/...
    carpeta = os.path.join(BASE_ARCHIVOS, "documentos", tipo, numero)
    os.makedirs(carpeta, exist_ok=True)

    nombre = archivo.filename
    ruta_completa = os.path.join(carpeta, nombre)
    if os.path.exists(ruta_completa):
        ts = datetime.now().strftime("%H%M%S")
        base, ext = os.path.splitext(nombre)
        nombre = f"{base}_{ts}{ext}"
        ruta_completa = os.path.join(carpeta, nombre)

    with open(ruta_completa, "wb") as dest:
        shutil.copyfileobj(archivo.file, dest)

    return os.path.join("documentos", tipo, numero, nombre)


def dias_habiles_transcurridos(fecha_inicio: datetime) -> int:
    """Calcula días hábiles (lunes-viernes) entre fecha_inicio y hoy."""
    hoy = date.today()
    inicio = fecha_inicio.date() if isinstance(fecha_inicio, datetime) else fecha_inicio
    count = 0
    current = inicio
    while current <= hoy:
        if current.weekday() < 5:  # 0=lunes ... 4=viernes
            count += 1
        current = date.fromordinal(current.toordinal() + 1)
    return count
