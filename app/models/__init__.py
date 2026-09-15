# Importar todos los modelos para que SQLAlchemy los registre al crear tablas
from app.models.users import Usuario
from app.models.claims import Reclamacion, Archivo, HistorialMovimiento
from app.models.documents import Documento
from app.models.tokens import AccesoDirecto
