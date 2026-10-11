from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import Unidade
from app.schemas.unidade import UnidadeCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/unidades",
    tags=["Unidades"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_unidade(
    unidade: UnidadeCreate,
    usuario=Depends(
        exigir_perfil("Gerente_administrador")
    )
):
    db = SessionLocal()

    try:
        nova_unidade = Unidade(
            nome=unidade.nome,
            endereco=unidade.endereco,
            cidade=unidade.cidade,
            estado=unidade.estado
        )

        db.add(nova_unidade)
        db.commit()
        db.refresh(nova_unidade)

        return {
            "id_unidade": nova_unidade.id_unidade,
            "nome": nova_unidade.nome,
            "endereco": nova_unidade.endereco,
            "cidade": nova_unidade.cidade,
            "estado": nova_unidade.estado
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.get("")
def listar_unidades():
    db = SessionLocal()

    try:
        unidades = db.query(Unidade).all()

        return [
            {
                "id_unidade": unidade.id_unidade,
                "nome": unidade.nome,
                "endereco": unidade.endereco,
                "cidade": unidade.cidade,
                "estado": unidade.estado
            }
            for unidade in unidades
        ]

    finally:
        db.close()
