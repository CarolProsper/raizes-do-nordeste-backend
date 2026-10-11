from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, status


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Configure SECRET_KEY no arquivo .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def criar_hash_senha(senha: str) -> str:
    senha_bytes = senha.encode("utf-8")

    hash_senha = bcrypt.hashpw(
        senha_bytes,
        bcrypt.gensalt()
    )

    return hash_senha.decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(
        senha.encode("utf-8"),
        senha_hash.encode("utf-8")
    )



def criar_token_acesso(
    id_usuario: int,
    login: str,
    perfil: str,
    id_cliente: int | None = None
) -> str:

    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(id_usuario),
        "login": login,
        "perfil": perfil,
        "exp": expiracao
    }

    if id_cliente is not None:
        payload["id_cliente"] = id_cliente

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )



def obter_dados_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )