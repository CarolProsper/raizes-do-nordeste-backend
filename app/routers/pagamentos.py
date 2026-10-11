from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import Pagamento, Pedido, ItemPedido
from app.schemas.pagamento import PagamentoCreate
from app.core.auth import exigir_perfil
from pydantic import BaseModel
from typing import Literal

router = APIRouter(
    prefix="/pagamentos",
    tags=["Pagamentos"]
)

class ResultadoPagamento(BaseModel):
    resultado: Literal["Autorizado", "Recusado"]

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar tentativa de pagamento",
    description=(
        "Registra uma tentativa de pagamento simulada. "
        "O status é definido automaticamente como Pendente. "
        "O pedido permanece em Aguardando Pagamento até que "
        "uma futura integração externa confirme o resultado."
    ),
)
def criar_pagamento(
    pagamento: PagamentoCreate,
    usuario=Depends(
        exigir_perfil("Cliente", "Gerente_administrador", "Atendente")
    )
):
    db = SessionLocal()

    try:
        # Verifica se o pedido existe
        pedido = db.query(Pedido).filter(
            Pedido.numero == pagamento.id_pedido
        ).with_for_update().first()

        if pedido is None:
            raise HTTPException(
                status_code=404,
                detail="Pedido não encontrado"
            )

        if usuario.get("perfil") == "Cliente":
            id_cliente_token = usuario.get("id_cliente")

            if id_cliente_token is None:
                raise HTTPException(
                    status_code=403,
                    detail="Usuário não está vinculado a um cliente"
                )

            if pedido.id_cliente != int(id_cliente_token):
                raise HTTPException(
                    status_code=404,
                    detail="Pedido não encontrado"
                )

        if pedido.status == "Cancelado":
            raise HTTPException(
                status_code=409,
                detail="Não é possível pagar um pedido cancelado"
            )

        itens = db.query(ItemPedido).filter(
            ItemPedido.id_pedido == pagamento.id_pedido
        ).count()

        if itens == 0:
            raise HTTPException(
                status_code=409,
                detail="Não é possível pagar um pedido sem itens"
            )
        if pedido.status != "Aguardando Pagamento":
            raise HTTPException(
                status_code=409,
                detail="O pedido não está aguardando pagamento"
            )

        # Verifica se já existe pagamento autorizado
        pagamento_autorizado = db.query(Pagamento).filter(
            Pagamento.id_pedido == pagamento.id_pedido,
            Pagamento.status_pagamento == "Autorizado"
        ).first()

        if pagamento_autorizado is not None:
            raise HTTPException(
                status_code=409,
                detail="O pedido já possui um pagamento autorizado"
            )

        # Verifica se já existe pagamento pendente
        pagamento_pendente = db.query(Pagamento).filter(
            Pagamento.id_pedido == pagamento.id_pedido,
            Pagamento.status_pagamento == "Pendente"
        ).first()

        if pagamento_pendente is not None:
            raise HTTPException(
                status_code=409,
                detail="O pedido já possui um pagamento pendente"
            )

        novo_pagamento = Pagamento(
            id_pedido=pagamento.id_pedido,
            forma_pagamento=pagamento.forma_pagamento,
            status_pagamento="Pendente",
        )

        db.add(novo_pagamento)
        db.commit()
        db.refresh(novo_pagamento)

        return {
            "id_pagamento": novo_pagamento.id_pagamento,
            "id_pedido": novo_pagamento.id_pedido,
            "forma_pagamento": novo_pagamento.forma_pagamento,
            "status_pagamento": novo_pagamento.status_pagamento,
            "data_hora_pagamento": novo_pagamento.data_hora_pagamento
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.post("/{id_pagamento}/resultado")
def registrar_resultado_pagamento(
    id_pagamento: int,
    dados: ResultadoPagamento,
    usuario=Depends(
        exigir_perfil("Gerente_administrador", "Atendente")
    ),
):
    db = SessionLocal()

    try:
        pagamento = db.query(Pagamento).filter(
            Pagamento.id_pagamento == id_pagamento
        ).first()

        if pagamento is None:
            raise HTTPException(
                status_code=404,
                detail="Pagamento não encontrado",
            )

        pedido = db.query(Pedido).filter(
            Pedido.numero == pagamento.id_pedido
        ).with_for_update().first()

        if pedido is None:
            raise HTTPException(
                status_code=404,
                detail="Pedido não encontrado",
            )

        if pagamento.status_pagamento != "Pendente":
            raise HTTPException(
                status_code=409,
                detail="O pagamento não está pendente",
            )

        if pedido.status != "Aguardando Pagamento":
            raise HTTPException(
                status_code=409,
                detail="O pedido não está aguardando pagamento",
            )

        pagamento.status_pagamento = dados.resultado

        if dados.resultado == "Autorizado":
            pedido.status = "Em Preparação"

        db.commit()
        db.refresh(pagamento)

        return {
            "id_pagamento": pagamento.id_pagamento,
            "id_pedido": pagamento.id_pedido,
            "status_pagamento": pagamento.status_pagamento,
            "status_pedido": pedido.status,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.get("")
def listar_pagamentos(
    usuario=Depends(exigir_perfil("Gerente_administrador", "Atendente"))
):
    db = SessionLocal()

    try:
        pagamentos = db.query(Pagamento).all()

        return [
            {
                "id_pagamento": pagamento.id_pagamento,
                "id_pedido": pagamento.id_pedido,
                "forma_pagamento": pagamento.forma_pagamento,
                "status_pagamento": pagamento.status_pagamento,
                "data_hora_pagamento": pagamento.data_hora_pagamento
            }
            for pagamento in pagamentos
        ]

    finally:
        db.close()