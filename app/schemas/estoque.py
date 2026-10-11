from pydantic import BaseModel, Field


class EstoqueCreate(BaseModel):
    id_unidade: int
    id_produto: int
    quantidade: int = Field(ge=0)
    disponivel: bool = True