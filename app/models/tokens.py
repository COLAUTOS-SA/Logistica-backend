import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from app.core.database import Base


class AccesoDirecto(Base):
    """Token de acceso directo generado por correo — válido 72h, uso único."""
    __tablename__ = "acceso_directo"

    token      = Column(String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    email      = Column(String(150), nullable=False, index=True)
    redirigir_a = Column(String(500), nullable=False, default="/reclamaciones")
    creado_en  = Column(DateTime, default=datetime.utcnow)
    expira_en  = Column(DateTime, nullable=False)
    usado      = Column(Boolean,  default=False)
