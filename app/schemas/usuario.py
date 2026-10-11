from typing import Literal
from pydantic import BaseModel, Field, field_validator


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    login: str = Field(min_length=3, max_length=50)
    senha: str = Field(min_length=8)
    perfil: Literal[
        "Gerente_administrador",
        "Atendente",
        "Cozinha",
        "Cliente"
    ]

    @field_validator("nome", "login")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        valor = valor.strip()
        if len(valor) < 3:
            raise ValueError("Informe pelo menos 3 caracteres")
        return valor
