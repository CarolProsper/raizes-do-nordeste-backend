
from typing import Literal
from pydantic import BaseModel


class PagamentoCreate(BaseModel):
    id_pedido: int
    forma_pagamento: Literal[
        "Pix",
        "Dinheiro",
        "Cartão de Crédito",
        "Cartão de Débito",
    ]
