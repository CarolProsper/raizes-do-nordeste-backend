
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class ProdutoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    preco_unitario: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
    )

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O nome do produto é obrigatório")
        return valor
