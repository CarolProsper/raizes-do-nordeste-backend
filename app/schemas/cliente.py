from datetime import date

from pydantic import BaseModel, Field


class ClienteCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    cpf: str | None = Field(default=None, pattern=r"^\d{11}$")
    data_nascimento: date | None = None
    telefone: str | None = None
    email: str | None = None
    autoriza_email: bool = False
    autoriza_telefone: bool = False
    status: str = "Ativo"