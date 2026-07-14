from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime
from app.core.database import Base


class Documento(Base):
    """
    Manifiesto, Remesa, Inventario o Inventario de Traslado.
    tipo: manifiesto | remesa | inventario | inventario_traslado
    """
    __tablename__ = "documentos"

    id = Column(String(30), primary_key=True, index=True)   # DOC-001
    tipo = Column(String(50), nullable=False)
    numero = Column(String(100), nullable=False, index=True)
    fecha = Column(String(50), nullable=True)

    # Vínculo con vehículo (opcional para manifiestos)
    vin = Column(String(50), nullable=True, index=True)
    vehiculo = Column(String(200), nullable=True)

    # Vínculos cruzados
    manifiesto_no = Column(String(100), nullable=True)
    remesa_no = Column(String(100), nullable=True)

    # Archivo físico
    nombre_archivo = Column(String(255), nullable=True)
    ruta_relativa = Column(String(500), nullable=True)

    # Meta
    subido_por = Column(String(150), nullable=False)
    fecha_carga = Column(DateTime, default=datetime.utcnow)

    # Campos específicos de manifiesto
    transportadora = Column(String(100), nullable=True)
    origen = Column(String(100), nullable=True)
    destino = Column(String(100), nullable=True)
    conductor = Column(String(150), nullable=True)
    placa = Column(String(20), nullable=True)
    vehiculos_json = Column(Text, nullable=True)  # lista de VINs guardada como JSON string

    # Campos específicos de remesa
    peso = Column(String(50), nullable=True)
    remitente = Column(String(150), nullable=True)
    destinatario = Column(String(150), nullable=True)
