from fastapi import HTTPException


def recurso_nao_encontrado(recurso: str):
    raise HTTPException(
        status_code=404,
        detail=f"{recurso} não encontrado"
    )


def conflito(mensagem: str):
    raise HTTPException(
        status_code=409,
        detail=mensagem
    )