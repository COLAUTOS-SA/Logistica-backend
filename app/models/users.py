from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False)   # admin | asistente | colision
    sede = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True)
