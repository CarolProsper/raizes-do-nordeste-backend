from datetime import datetime

from pydantic import BaseModel


class MovimentacaoPontosCreate(BaseModel):
    id_fidelidade: int
    id_pedido: int | None = None
    quantidade_pontos: int
    tipo: str
    origem_movimentacao: str
    data_hora: datetime