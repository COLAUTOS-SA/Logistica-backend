from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import hash_password
from app.models.users import Usuario
from app.schemas.users import UsuarioResponse, UsuarioCreate, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).filter(Usuario.activo == True).all()


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(Usuario.email == payload.email.lower()).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")

    nuevo = Usuario(
        nombre=payload.nombre,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        rol=payload.rol,
        sede=payload.sede,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(usuario_id: int, payload: UsuarioUpdate, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.nombre is not None:
        user.nombre = payload.nombre.strip()
    if payload.email is not None:
        email = payload.email.strip().lower()
        existe = db.query(Usuario).filter(Usuario.email == email, Usuario.id != usuario_id).first()
        if existe:
            raise HTTPException(status_code=400, detail="Ese email ya está en uso por otro usuario")
        user.email = email
    if payload.password is not None and payload.password.strip():
        user.password_hash = hash_password(payload.password)
    if payload.rol is not None:
        user.rol = payload.rol
    if payload.sede is not None:
        user.sede = payload.sede

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.activo = False
    db.commit()
