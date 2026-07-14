from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# ── Archivos ────────────────────────────────────────────────────────────────

class ArchivoResponse(BaseModel):
    id: int
    categoria: str          # foto | video | soporte | cotizacion | factura | certificado
    nombre_original: str
    url: str                # URL pública para descargar/ver el archivo
    subido_por: str
    fecha_subida: datetime

    class Config:
        from_attributes = True


# ── Historial ────────────────────────────────────────────────────────────────

class HistorialItem(BaseModel):
    id: int
    fecha: datetime
    accion: str
    usuario: str
    detalle: Optional[str] = None

    class Config:
        from_attributes = True


# ── Reclamación ──────────────────────────────────────────────────────────────

class ReclamacionCreate(BaseModel):
    vin: str
    vehiculo: str
    tipo_novedad: str
    descripcion: str
    transportadora: str = "BERGE Vigía"
    no_remesa: str
    no_manifiesto: str
    sede: Optional[str] = None
    reportado_por: str
    responsable_actual: str
    dias_limite: int = 10


class ReclamacionResponse(BaseModel):
    id: str
    vin: str
    vehiculo: str
    tipo_novedad: str
    descripcion: str
    transportadora: str
    no_remesa: str
    no_manifiesto: str
    sede: Optional[str] = None
    estado: str
    fecha_reporte: datetime
    fecha_radicacion: Optional[datetime] = None
    no_radicado_vigia: Optional[str] = None
    cotizacion: Optional[str] = None
    reportado_por: str
    responsable_actual: str
    dias_limite: int
    dias_habiles: int           # calculado dinámicamente
    archivos: List[ArchivoResponse] = []
    historial: List[HistorialItem] = []

    class Config:
        from_attributes = True


class CambiarEstadoRequest(BaseModel):
    nuevo_estado: str
    usuario: str
    detalle: Optional[str] = None


class SubirCotizacionRequest(BaseModel):
    valor: str
    descripcion: Optional[str] = None
    usuario: str


class SubirFacturaRequest(BaseModel):
    descripcion: Optional[str] = None
    usuario: str
