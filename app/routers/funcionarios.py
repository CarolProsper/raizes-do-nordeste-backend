from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import Funcionario, Unidade
from app.schemas.funcionario import FuncionarioCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/funcionarios",
    tags=["Funcionários"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_funcionario(
    funcionario: FuncionarioCreate,
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        # Verifica se a unidade existe
        unidade = db.query(Unidade).filter(
            Unidade.id_unidade == funcionario.id_unidade
        ).first()

        if unidade is None:
            raise HTTPException(
                status_code=404,
                detail="Unidade não encontrada"
            )

        novo_funcionario = Funcionario(
            id_unidade=funcionario.id_unidade,
            nome=funcionario.nome,
            funcao=funcionario.funcao
        )

        db.add(novo_funcionario)
        db.commit()
        db.refresh(novo_funcionario)

        return {
            "id_funcionario": novo_funcionario.id_funcionario,
            "id_unidade": novo_funcionario.id_unidade,
            "nome": novo_funcionario.nome,
            "funcao": novo_funcionario.funcao
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
def listar_funcionarios(
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        funcionarios = db.query(Funcionario).all()

        return [
            {
                "id_funcionario": funcionario.id_funcionario,
                "id_unidade": funcionario.id_unidade,
                "nome": funcionario.nome,
                "funcao": funcionario.funcao
            }
            for funcionario in funcionarios
        ]

    finally:
        db.close()