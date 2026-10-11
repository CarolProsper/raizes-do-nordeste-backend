from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import Estoque, Unidade, Produto
from app.schemas.estoque import EstoqueCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/estoque",
    tags=["Estoque"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_estoque(
    estoque: EstoqueCreate,
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        # Verifica se a unidade existe
        unidade = db.query(Unidade).filter(
            Unidade.id_unidade == estoque.id_unidade
        ).first()

        if unidade is None:
            raise HTTPException(
                status_code=404,
                detail="Unidade não encontrada"
            )

        # Verifica se o produto existe
        produto = db.query(Produto).filter(
            Produto.id_produto == estoque.id_produto
        ).first()

        if produto is None:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado"
            )

        # Verifica se já existe estoque desse produto nessa unidade
        estoque_existente = db.query(Estoque).filter(
            Estoque.id_unidade == estoque.id_unidade,
            Estoque.id_produto == estoque.id_produto
        ).first()

        if estoque_existente is not None:
            raise HTTPException(
                status_code=409,
                detail="Já existe estoque para este produto nesta unidade"
            )

        novo_estoque = Estoque(
            id_unidade=estoque.id_unidade,
            id_produto=estoque.id_produto,
            quantidade=estoque.quantidade,
            disponivel=estoque.disponivel
        )

        db.add(novo_estoque)
        db.commit()
        db.refresh(novo_estoque)

        return {
            "id_estoque": novo_estoque.id_estoque,
            "id_unidade": novo_estoque.id_unidade,
            "id_produto": novo_estoque.id_produto,
            "quantidade": novo_estoque.quantidade,
            "disponivel": novo_estoque.disponivel
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
def listar_estoque(
    usuario=Depends(exigir_perfil("Gerente_administrador", "Atendente"))
):
    db = SessionLocal()

    try:
        estoques = db.query(Estoque).all()

        return [
            {
                "id_estoque": estoque.id_estoque,
                "id_unidade": estoque.id_unidade,
                "id_produto": estoque.id_produto,
                "quantidade": estoque.quantidade,
                "disponivel": estoque.disponivel
            }
            for estoque in estoques
        ]

    finally:
        db.close()