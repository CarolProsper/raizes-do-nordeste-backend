from fastapi import APIRouter, status, Depends, HTTPException, Query
from app.database.database import SessionLocal
from app.database.models import Produto, Estoque, Unidade
from app.schemas.produto import ProdutoCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"]
)

@router.post("", status_code=status.HTTP_201_CREATED)
def criar_produto(
    produto: ProdutoCreate,
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        novo_produto = Produto(
            nome=produto.nome,
            preco_unitario=produto.preco_unitario
        )

        db.add(novo_produto)
        db.commit()
        db.refresh(novo_produto)

        return {
            "id_produto": novo_produto.id_produto,
            "nome": novo_produto.nome,
            "preco_unitario": novo_produto.preco_unitario
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.get("")
def listar_produtos():
    db = SessionLocal()

    try:
        produtos = db.query(Produto).all()

        return [
            {
                "id_produto": produto.id_produto,
                "nome": produto.nome,
                "preco_unitario": produto.preco_unitario
            }
            for produto in produtos
        ]

    finally:
        db.close()


@router.get("/disponibilidade")
def consultar_disponibilidade(
    id_unidade: int = Query(..., gt=0)
):
    db = SessionLocal()

    try:
        unidade = db.query(Unidade).filter(
            Unidade.id_unidade == id_unidade
        ).first()

        if unidade is None:
            raise HTTPException(
                status_code=404,
                detail="Unidade não encontrada"
            )

        produtos = db.query(Produto).all()

        estoques = db.query(Estoque).filter(
            Estoque.id_unidade == id_unidade
        ).all()

        estoque_por_produto = {
            estoque.id_produto: estoque
            for estoque in estoques
        }

        resultado = []

        for produto in produtos:
            estoque = estoque_por_produto.get(
                produto.id_produto
            )

            quantidade = (
                estoque.quantidade
                if estoque is not None
                else 0
            )

            disponivel = (
                estoque is not None
                and estoque.disponivel
                and quantidade > 0
            )

            resultado.append({
                "id_produto": produto.id_produto,
                "nome": produto.nome,
                "preco_unitario": produto.preco_unitario,
                "id_unidade": id_unidade,
                "quantidade_disponivel": quantidade,
                "disponivel": disponivel
            })

        return resultado

    finally:
        db.close()
