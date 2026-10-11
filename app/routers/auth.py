from fastapi import APIRouter, HTTPException, status

from app.database.database import SessionLocal
from app.database.models import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import (
    verificar_senha,
    criar_token_acesso
)


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(dados: LoginRequest):

    db = SessionLocal()

    try:
        usuario = db.query(Usuario).filter(
            Usuario.login == dados.login
        ).first()

        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login ou senha inválidos"
            )

        if not usuario.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )

        if not verificar_senha(
            dados.senha,
            usuario.senha_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login ou senha inválidos"
            )

        token = criar_token_acesso(
            id_usuario=usuario.id_usuario,
            login=usuario.login,
            perfil=usuario.perfil,
            id_cliente=usuario.id_cliente
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    finally:
        db.close()