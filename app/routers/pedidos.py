from fastapi import APIRouter, status, HTTPException, Header, Depends
from app.database.database import SessionLocal
from app.database.models import (
    Pedido,
    Cliente,
    Unidade,
    ItemPedido,
    Estoque,
    Pagamento,
    Produto
)
from app.schemas.pedido import PedidoCreate
from app.core.auth import exigir_perfil
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"]
)


@router.get("/meus")
def consultar_meus_pedidos(
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

        pedidos = db.query(Pedido).filter(
            Pedido.id_cliente == int(id_cliente_token)
        ).order_by(
            Pedido.data_hora_pedido.desc()
        ).all()

        return [
            {
                "numero": pedido.numero,
                "id_unidade": pedido.id_unidade,
                "canal_pedido": pedido.canal_pedido,
                "status": pedido.status,
                "data_hora_pedido": pedido.data_hora_pedido
            }
            for pedido in pedidos
        ]

    finally:
        db.close()


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_pedido(
    pedido: PedidoCreate,
    idempotency_key: str = Header(...),
    usuario=Depends(
        exigir_perfil("Cliente", "Gerente_administrador", "Atendente")
    )
):
    db = SessionLocal()

    try:
        id_cliente_pedido = pedido.id_cliente

        if usuario.get("perfil") == "Cliente":
            id_cliente_token = usuario.get("id_cliente")

            if id_cliente_token is None:
                raise HTTPException(
                    status_code=403,
                    detail="Usuário não está vinculado a um cliente"
                )

            id_cliente_pedido = int(id_cliente_token)

        pedido_existente = db.query(Pedido).filter(
            Pedido.chave_idempotencia == idempotency_key
        ).first()

        if pedido_existente:
            if (
                pedido_existente.id_cliente != id_cliente_pedido
                or pedido_existente.id_unidade != pedido.id_unidade
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Chave de idempotência já utilizada em outro pedido"
                )

            return {
                "numero": pedido_existente.numero,
                "id_cliente": pedido_existente.id_cliente,
                "id_unidade": pedido_existente.id_unidade,
                "canal_pedido": pedido_existente.canal_pedido,
                "status": pedido_existente.status,
                "data_hora_pedido": pedido_existente.data_hora_pedido,
                "motivo_cancelamento": pedido_existente.motivo_cancelamento
            }

        if not pedido.itens:
            raise HTTPException(
                status_code=422,
                detail="O pedido deve conter pelo menos um produto"
            )

        cliente = db.query(Cliente).filter(
            Cliente.id_cliente == id_cliente_pedido
        ).first()

        if cliente is None:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado"
            )

        unidade = db.query(Unidade).filter(
            Unidade.id_unidade == pedido.id_unidade
        ).first()

        if unidade is None:
            raise HTTPException(
                status_code=404,
                detail="Unidade não encontrada"
            )

        # Agrupa quantidades repetidas do mesmo produto.
        quantidades = {}
        for item in pedido.itens:
            quantidades[item.id_produto] = (
                quantidades.get(item.id_produto, 0) + item.quantidade
            )

        # Valida produtos e bloqueia os registros de estoque.
        produtos = {}
        estoques = {}

        for id_produto in sorted(quantidades):
            produto = db.query(Produto).filter(
                Produto.id_produto == id_produto
            ).first()

            if produto is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Produto {id_produto} não encontrado"
                )

            estoque = db.query(Estoque).filter(
                Estoque.id_unidade == pedido.id_unidade,
                Estoque.id_produto == id_produto
            ).with_for_update().first()

            if estoque is None or not estoque.disponivel:
                raise HTTPException(
                    status_code=409,
                    detail=f"Produto {id_produto} indisponível nesta unidade"
                )

            if estoque.quantidade < quantidades[id_produto]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Estoque insuficiente para o produto {id_produto}"
                )

            produtos[id_produto] = produto
            estoques[id_produto] = estoque

        novo_pedido = Pedido(
            id_cliente=id_cliente_pedido,
            id_unidade=pedido.id_unidade,
            canal_pedido=pedido.canal_pedido,
            status="Aguardando Pagamento",
            data_hora_pedido=pedido.data_hora_pedido,
            motivo_cancelamento=None,
            chave_idempotencia=idempotency_key
        )

        db.add(novo_pedido)
        db.flush()

        # Cria todos os itens e desconta o estoque na mesma transação.
        for item in pedido.itens:
            produto = produtos[item.id_produto]

            db.add(ItemPedido(
                id_pedido=novo_pedido.numero,
                id_produto=item.id_produto,
                quantidade=item.quantidade,
                preco_unitario=produto.preco_unitario
            ))

        for id_produto, quantidade in quantidades.items():
            estoques[id_produto].quantidade -= quantidade

        db.commit()
        db.refresh(novo_pedido)

        return {
            "numero": novo_pedido.numero,
            "id_cliente": novo_pedido.id_cliente,
            "id_unidade": novo_pedido.id_unidade,
            "canal_pedido": novo_pedido.canal_pedido,
            "status": novo_pedido.status,
            "data_hora_pedido": novo_pedido.data_hora_pedido,
            "motivo_cancelamento": novo_pedido.motivo_cancelamento,
            "itens": [
                {
                    "id_produto": item.id_produto,
                    "quantidade": item.quantidade,
                    "preco_unitario": produtos[item.id_produto].preco_unitario
                }
                for item in pedido.itens
            ]
        }

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito ao criar pedido. Verifique a chave de idempotência e tente novamente."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.get("")
def listar_pedidos(
        usuario=Depends(
        exigir_perfil(
            "Gerente_administrador",
            "Atendente",
            "Cozinha",
        )
    ),
):
    db = SessionLocal()

    try:
        pedidos = db.query(Pedido).all()

        return [
            {
                "numero": pedido.numero,
                "id_cliente": pedido.id_cliente,
                "id_unidade": pedido.id_unidade,
                "canal_pedido": pedido.canal_pedido,
                "status": pedido.status,
                "data_hora_pedido": pedido.data_hora_pedido,
                "motivo_cancelamento": pedido.motivo_cancelamento
            }
            for pedido in pedidos
        ]

    finally:
        db.close()

@router.get("/{numero}/total")
def consultar_total_pedido(
    numero: int,
    usuario=Depends(
        exigir_perfil("Cliente", "Gerente_administrador", "Atendente")
    )
):
    db = SessionLocal()

    try:
        consulta = db.query(Pedido).filter(
            Pedido.numero == numero
        )

        if usuario.get("perfil") == "Cliente":
            id_cliente_token = usuario.get("id_cliente")

            if id_cliente_token is None:
                raise HTTPException(
                    status_code=403,
                    detail="Usuário não está vinculado a um cliente"
                )

            consulta = consulta.filter(
                Pedido.id_cliente == int(id_cliente_token)
            )

        pedido = consulta.first()

        if pedido is None:
            raise HTTPException(
                status_code=404,
                detail="Pedido não encontrado"
            )

        itens = db.query(ItemPedido).filter(
            ItemPedido.id_pedido == numero
        ).all()

        total = sum(
            item.quantidade * item.preco_unitario
            for item in itens
        )

        return {
            "numero_pedido": numero,
            "itens": [
                {
                    "id_produto": item.id_produto,
                    "quantidade": item.quantidade,
                    "preco_unitario": item.preco_unitario,
                    "subtotal": round(
                        item.quantidade * item.preco_unitario, 2
                    )
                }
                for item in itens
            ],
            "valor_total": round(total, 2)
        }

    finally:
        db.close()



@router.patch("/{numero}/status")
def atualizar_status_pedido(
    numero: int,
    novo_status: str,
    usuario=Depends(
        exigir_perfil(
            "Gerente_administrador",
            "Atendente",
            "Cozinha",
        )
    ),
):
    db = SessionLocal()

    try:
        pedido = db.query(Pedido).filter(
            Pedido.numero == numero
        ).with_for_update().first()

        if pedido is None:
            raise HTTPException(
                status_code=404,
                detail="Pedido não encontrado",
            )

        # A cozinha só pode concluir a preparação.
        if usuario.get("perfil") == "Cozinha":
            if (
                pedido.status != "Em Preparação"
                or novo_status != "Pronto"
            ):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "A cozinha só pode alterar o status "
                        "de Em Preparação para Pronto"
                    ),
                )

        transicoes = {
            "Em Preparação": ["Pronto"],
            "Pronto": ["Entregue"],
        }

        permitidos = transicoes.get(pedido.status, [])

        if novo_status not in permitidos:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Transição inválida: {pedido.status} "
                    f"para {novo_status}"
                ),
            )

        pedido.status = novo_status
        db.commit()
        db.refresh(pedido)

        return {
            "numero": pedido.numero,
            "status": pedido.status,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



@router.patch("/{numero}/cancelar")
def cancelar_pedido(
    numero: int,
    motivo: str = "",
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        motivo = motivo.strip()

        if not motivo:
            raise HTTPException(
                status_code=422,
                detail="O motivo do cancelamento é obrigatório"
            )

        pedido = db.query(Pedido).filter(
            Pedido.numero == numero
        ).with_for_update().first()

        if pedido is None:
            raise HTTPException(
                status_code=404,
                detail="Pedido não encontrado"
            )

        if pedido.status == "Cancelado":
            raise HTTPException(
                status_code=409,
                detail="Pedido já está cancelado"
            )
        pagamento_autorizado = db.query(Pagamento).filter(
            Pagamento.id_pedido == numero,
            Pagamento.status_pagamento == "Autorizado"
        ).first()

        if pagamento_autorizado is not None:
            raise HTTPException(
                status_code=409,
                detail="Não é possível cancelar um pedido com pagamento autorizado"
        )

        itens = db.query(ItemPedido).filter(
            ItemPedido.id_pedido == numero
        ).all()

        # Devolve ao estoque as quantidades dos itens
        for item in itens:
            estoque = db.query(Estoque).filter(
                Estoque.id_unidade == pedido.id_unidade,
                Estoque.id_produto == item.id_produto
            ).with_for_update().first()

            if estoque is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Estoque não encontrado para o produto {item.id_produto}"
                )

            estoque.quantidade += item.quantidade

        pedido.status = "Cancelado"
        pedido.motivo_cancelamento = motivo

        db.commit()
        db.refresh(pedido)

        return {
            "numero": pedido.numero,
            "status": pedido.status,
            "motivo_cancelamento": pedido.motivo_cancelamento
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
