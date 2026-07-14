from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Reclamacion(Base):
    __tablename__ = "reclamaciones"

    # Identificación
    id = Column(String(30), primary_key=True, index=True)   # REC-2026-001
    vin = Column(String(50), nullable=False, index=True)
    vehiculo = Column(String(200), nullable=False)
    tipo_novedad = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)

    # Logística
    transportadora = Column(String(100), default="BERGE Vigía")
    no_remesa = Column(String(100), nullable=False)
    no_manifiesto = Column(String(100), nullable=False)
    sede = Column(String(100), nullable=True)

    # Flujo
    # Estados: abierta | en_gestion | radicada_vigia | aprobada | en_facturacion | cerrada
    estado = Column(String(50), default="abierta")

    # Fechas
    fecha_reporte = Column(DateTime, default=datetime.utcnow)
    fecha_radicacion = Column(DateTime, nullable=True)

    # Datos Vigía
    no_radicado_vigia = Column(String(100), nullable=True)

    # Cotización / Factura (valor textual p.ej. "$850.000")
    cotizacion = Column(String(100), nullable=True)

    # Responsables
    reportado_por = Column(String(150), nullable=False)
    responsable_actual = Column(String(150), nullable=False)

    # Días hábiles límite (normalmente 10)
    dias_limite = Column(Integer, default=10)

    # Relaciones
    archivos = relationship(
        "Archivo", back_populates="reclamacion",
        cascade="all, delete-orphan"
    )
    historial = relationship(
        "HistorialMovimiento", back_populates="reclamacion",
        order_by="HistorialMovimiento.fecha",
        cascade="all, delete-orphan"
    )


class Archivo(Base):
    """Registra cada archivo subido y su ruta en disco."""
    __tablename__ = "archivos"

    id = Column(Integer, primary_key=True, index=True)
    reclamacion_id = Column(String(30), ForeignKey("reclamaciones.id"), nullable=False)

    # categoria: foto | video | soporte | cotizacion | factura | certificado
    categoria = Column(String(50), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    ruta_relativa = Column(String(500), nullable=False)
    subido_por = Column(String(150), nullable=False)
    fecha_subida = Column(DateTime, default=datetime.utcnow)

    reclamacion = relationship("Reclamacion", back_populates="archivos")


class HistorialMovimiento(Base):
    """Traza cada cambio de estado o acción sobre una reclamación."""
    __tablename__ = "historial"

    id = Column(Integer, primary_key=True, index=True)
    reclamacion_id = Column(String(30), ForeignKey("reclamaciones.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    accion = Column(String(200), nullable=False)
    usuario = Column(String(150), nullable=False)
    detalle = Column(Text, nullable=True)

    reclamacion = relationship("Reclamacion", back_populates="historial")
