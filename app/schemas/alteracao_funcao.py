from datetime import datetime

from pydantic import BaseModel


class AlteracaoFuncaoCreate(BaseModel):
    id_funcionario: int
    funcao_nova: str