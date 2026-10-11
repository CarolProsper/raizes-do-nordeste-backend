from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import (
    MovimentacaoPontos,
    Fidelidade,
    Pedido
)
from app.schemas.movimentacao_pontos import MovimentacaoPontosCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/movimentacao_pontos",
    tags=["Movimentação de Pontos"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_movimentacao_pontos(
    movimentacao: MovimentacaoPontosCreate,
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        # Verifica se a fidelidade existe
        fidelidade = db.query(Fidelidade).filter(
            Fidelidade.id_fidelidade == movimentacao.id_fidelidade
        ).first()

        if fidelidade is None:
            raise HTTPException(
                status_code=404,
                detail="Fidelidade não encontrada"
            )

        # O pedido é opcional
        if movimentacao.id_pedido is not None:
            pedido = db.query(Pedido).filter(
                Pedido.numero == movimentacao.id_pedido
            ).first()

            if pedido is None:
                raise HTTPException(
                    status_code=404,
                    detail="Pedido não encontrado"
                )

        nova_movimentacao = MovimentacaoPontos(
            id_fidelidade=movimentacao.id_fidelidade,
            id_pedido=movimentacao.id_pedido,
            quantidade_pontos=movimentacao.quantidade_pontos,
            tipo=movimentacao.tipo,
            origem_movimentacao=movimentacao.origem_movimentacao,
        )

        db.add(nova_movimentacao)
        db.commit()
        db.refresh(nova_movimentacao)

        return {
            "id_mov_pontos": nova_movimentacao.id_mov_pontos,
            "id_fidelidade": nova_movimentacao.id_fidelidade,
            "id_pedido": nova_movimentacao.id_pedido,
            "quantidade_pontos": nova_movimentacao.quantidade_pontos,
            "tipo": nova_movimentacao.tipo,
            "origem_movimentacao": nova_movimentacao.origem_movimentacao,
            "data_hora": nova_movimentacao.data_hora
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
def listar_movimentacoes_pontos(
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        movimentacoes = db.query(MovimentacaoPontos).all()

        return [
            {
                "id_mov_pontos": movimentacao.id_mov_pontos,
                "id_fidelidade": movimentacao.id_fidelidade,
                "id_pedido": movimentacao.id_pedido,
                "quantidade_pontos": movimentacao.quantidade_pontos,
                "tipo": movimentacao.tipo,
                "origem_movimentacao": movimentacao.origem_movimentacao,
                "data_hora": movimentacao.data_hora
            }
            for movimentacao in movimentacoes
        ]

    finally:
        db.close()