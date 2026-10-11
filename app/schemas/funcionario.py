from pydantic import BaseModel


class FuncionarioCreate(BaseModel):
    id_unidade: int
    nome: str
    funcao: str