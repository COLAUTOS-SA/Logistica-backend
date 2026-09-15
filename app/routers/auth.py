from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.users import Usuario
from app.models.tokens import AccesoDirecto
from app.schemas.users import LoginRequest, TokenResponse, UsuarioResponse

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(
        Usuario.email == payload.email.lower().strip(),
        Usuario.activo == True
    ).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    token = create_access_token({"sub": str(user.id), "rol": user.rol})

    return TokenResponse(
        access_token=token,
        usuario=UsuarioResponse.model_validate(user)
    )


@router.get("/acceso/{token}")
def acceder_con_token(token: str, db: Session = Depends(get_db)):
    """
    Valida un magic link y retorna la sesión del usuario.
    Cada token es de uso único y válido por 72 horas.
    """
    registro = db.query(AccesoDirecto).filter(AccesoDirecto.token == token).first()

    if not registro:
        raise HTTPException(status_code=404, detail="Enlace inválido")
    if registro.usado:
        raise HTTPException(status_code=410, detail="Este enlace ya fue utilizado. Inicia sesión normalmente.")
    if registro.expira_en < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Este enlace expiró (válido 72 horas). Inicia sesión normalmente.")

    user = db.query(Usuario).filter(
        Usuario.email == registro.email,
        Usuario.activo.is_(True)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")

    registro.usado = True
    db.commit()

    return {
        "usuario": {
            "id":     user.id,
            "nombre": user.nombre,
            "email":  user.email,
            "rol":    user.rol,
            "sede":   user.sede,
            "activo": user.activo,
        },
        "redirigir_a": registro.redirigir_a,
    }
