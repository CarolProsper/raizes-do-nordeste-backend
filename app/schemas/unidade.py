from pydantic import BaseModel, Field, field_validator


class UnidadeCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    endereco: str = Field(min_length=1, max_length=200)
    cidade: str = Field(min_length=1, max_length=100)
    estado: str = Field(min_length=2, max_length=2)

    @field_validator("nome", "endereco", "cidade", "estado")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O campo não pode ficar vazio")
        return valor