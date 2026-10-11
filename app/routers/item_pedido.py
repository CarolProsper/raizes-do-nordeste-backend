from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import (
    ItemPedido,
    Pedido,
    Produto,
    Estoque
)
from app.schemas.item_pedido import ItemPedidoCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/item_pedido",
    tags=["Itens do Pedido"]
)


@router.get("/meu/{numero}")
def consultar_itens_meu_pedido(
    numero: int,
    usuario=Depends(exigir_perfil("Cliente"))
):
    db = SessionLocal()

    try:
        id_cliente_token = usuario.get("id_cliente")

        if id_cliente_token is None:
            raise HTTPException(
                status_code=403,
                detail="Usuário não está vinculado a um cliente"
            )

        pedido = db.query(Pedido).filter(
            Pedido.numero == numero,
            Pedido.id_cliente == int(id_cliente_token)
        ).first()

        if pedido is None:
            raise HTTPException(
                status_code=404,
                detail="Pedido não encontrado"
            )

        itens = db.query(ItemPedido).filter(
            ItemPedido.id_pedido == numero
        ).all()

        return [
            {
                "id_item_pedido": item.id_item_pedido,
                "id_pedido": item.id_pedido,
                "id_produto": item.id_produto,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario
            }
            for item in itens
        ]

    finally:
        db.close()


@router.post("")
def criar_item_pedido(
    dados: ItemPedidoCreate,
    usuario=Depends(exigir_perfil("Gerente_administrador", "Atendente"))
):
    db = SessionLocal()

    try:
        pedido = db.query(Pedido).filter(
            Pedido.numero == dados.id_pedido
        ).with_for_update().first()

        if pedido is None:
            raise HTTPException(
                status_code=404,
                detail="Pedido não encontrado"
            )

        produto = db.query(Produto).filter(
            Produto.id_produto == dados.id_produto
        ).first()

        if produto is None:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado"
            )

        if pedido.status != "Aguardando Pagamento":
            raise HTTPException(
                status_code=409,
                detail="Só é possível adicionar itens a pedidos aguardando pagamento"
            )

        estoque = db.query(Estoque).filter(
            Estoque.id_unidade == pedido.id_unidade,
            Estoque.id_produto == dados.id_produto
        ).with_for_update().first()

        if estoque is None:
            raise HTTPException(
                status_code=404,
                detail="Produto não possui estoque cadastrado para esta unidade"
            )

        if not estoque.disponivel:
            raise HTTPException(
                status_code=409,
                detail="Produto indisponível nesta unidade"
            )

        if estoque.quantidade < dados.quantidade:
            raise HTTPException(
                status_code=409,
                detail="Estoque insuficiente"
            )

        novo_item = ItemPedido(
            id_pedido=dados.id_pedido,
            id_produto=dados.id_produto,
            quantidade=dados.quantidade,
            preco_unitario=produto.preco_unitario
        )

        estoque.quantidade -= dados.quantidade

        db.add(novo_item)
        db.commit()
        db.refresh(novo_item)

        return {
            "id_item_pedido": novo_item.id_item_pedido,
            "id_pedido": novo_item.id_pedido,
            "id_produto": novo_item.id_produto,
            "quantidade": novo_item.quantidade,
            "preco_unitario": novo_item.preco_unitario
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
def listar_itens_pedido(
    usuario=Depends(exigir_perfil("Gerente_administrador", "Atendente"))
):
    db = SessionLocal()

    try:
        itens = db.query(ItemPedido).all()

        return [
            {
                "id_item_pedido": item.id_item_pedido,
                "id_pedido": item.id_pedido,
                "id_produto": item.id_produto,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario
            }
            for item in itens
        ]

    finally:
        db.close()