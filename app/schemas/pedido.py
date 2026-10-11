from datetime import datetime
from pydantic import BaseModel, Field


class ItemPedidoEntrada(BaseModel):
    id_produto: int
    quantidade: int = Field(gt=0)


class PedidoCreate(BaseModel):
    id_cliente: int
    id_unidade: int
    canal_pedido: str
    status: str
    data_hora_pedido: datetime
    motivo_cancelamento: str | None = None
    itens: list[ItemPedidoEntrada] = Field(default_factory=list)
