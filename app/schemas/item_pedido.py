from pydantic import BaseModel, Field


class ItemPedidoCreate(BaseModel):
    id_pedido: int
    id_produto: int
    quantidade: int = Field(gt=0)
