from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class DocumentoResponse(BaseModel):
    id: str
    tipo: str
    numero: str
    fecha: Optional[str] = None
    vin: Optional[str] = None
    vehiculo: Optional[str] = None
    manifiesto_no: Optional[str] = None
    remesa_no: Optional[str] = None
    nombre_archivo: Optional[str] = None
    url_archivo: Optional[str] = None
    subido_por: str
    fecha_carga: datetime
    transportadora: Optional[str] = None
    origen: Optional[str] = None
    destino: Optional[str] = None
    conductor: Optional[str] = None
    placa: Optional[str] = None
    vehiculos: Optional[List[str]] = None   # lista de VINs (para manifiestos)
    peso: Optional[str] = None
    remitente: Optional[str] = None
    destinatario: Optional[str] = None

    class Config:
        from_attributes = True
