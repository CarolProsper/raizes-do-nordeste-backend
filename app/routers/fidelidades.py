from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import Fidelidade, Cliente
from app.schemas.fidelidade import FidelidadeCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/fidelidades",
    tags=["Fidelidades"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_fidelidade(
    fidelidade: FidelidadeCreate,
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        # Verifica se o cliente existe
        cliente = db.query(Cliente).filter(
            Cliente.id_cliente == fidelidade.id_cliente
        ).first()

        if cliente is None:
            raise HTTPException(
                status_code=404,
                detail="Cliente não encontrado"
            )

        # Verifica se o cliente já possui fidelidade
        fidelidade_existente = db.query(Fidelidade).filter(
            Fidelidade.id_cliente == fidelidade.id_cliente
        ).first()

        if fidelidade_existente is not None:
            raise HTTPException(
                status_code=409,
                detail="O cliente já possui uma fidelidade"
            )

        nova_fidelidade = Fidelidade(
            id_cliente=fidelidade.id_cliente,
            status=fidelidade.status,
            data_exclusao=fidelidade.data_exclusao
        )

        db.add(nova_fidelidade)
        db.commit()
        db.refresh(nova_fidelidade)

        return {
            "id_fidelidade": nova_fidelidade.id_fidelidade,
            "id_cliente": nova_fidelidade.id_cliente,
            "status": nova_fidelidade.status,
            "data_adesao": nova_fidelidade.data_adesao,
            "data_exclusao": nova_fidelidade.data_exclusao
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
def listar_fidelidades(
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        fidelidades = db.query(Fidelidade).all()

        return [
            {
                "id_fidelidade": fidelidade.id_fidelidade,
                "id_cliente": fidelidade.id_cliente,
                "status": fidelidade.status,
                "data_adesao": fidelidade.data_adesao,
                "data_exclusao": fidelidade.data_exclusao
            }
            for fidelidade in fidelidades
        ]

    finally:
        db.close()