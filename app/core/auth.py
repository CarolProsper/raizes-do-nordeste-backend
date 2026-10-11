from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import obter_dados_token


security = HTTPBearer()


def obter_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    dados = obter_dados_token(token)

    if "sub" not in dados:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    return dados


def exigir_perfil(*perfis_permitidos):

    def verificar_perfil(
        usuario=Depends(obter_usuario_atual)
    ):
        perfil = usuario.get("perfil")

        if perfil not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário sem permissão para esta operação"
            )

        return usuario

    return verificar_perfil
