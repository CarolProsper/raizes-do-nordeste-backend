from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import Auditoria, Funcionario
from app.schemas.auditoria import AuditoriaCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/auditorias",
    tags=["Auditorias"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_auditoria(
    auditoria: AuditoriaCreate,
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        # Verifica se o funcionário existe
        funcionario = db.query(Funcionario).filter(
            Funcionario.id_funcionario == auditoria.id_funcionario
        ).first()

        if funcionario is None:
            raise HTTPException(
                status_code=404,
                detail="Funcionário não encontrado"
            )

        nova_auditoria = Auditoria(
            id_funcionario=auditoria.id_funcionario,
            tipo_ocorrencia=auditoria.tipo_ocorrencia,
            objeto_ocorrencia=auditoria.objeto_ocorrencia,
            registro_ocorrencia=auditoria.registro_ocorrencia,
        )

        db.add(nova_auditoria)
        db.commit()
        db.refresh(nova_auditoria)

        return {
            "id_auditoria": nova_auditoria.id_auditoria,
            "id_funcionario": nova_auditoria.id_funcionario,
            "tipo_ocorrencia": nova_auditoria.tipo_ocorrencia,
            "objeto_ocorrencia": nova_auditoria.objeto_ocorrencia,
            "registro_ocorrencia": nova_auditoria.registro_ocorrencia,
            "data_hora_ocorrencia": nova_auditoria.data_hora_ocorrencia
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
def listar_auditorias(
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        auditorias = db.query(Auditoria).all()

        return [
            {
                "id_auditoria": auditoria.id_auditoria,
                "id_funcionario": auditoria.id_funcionario,
                "tipo_ocorrencia": auditoria.tipo_ocorrencia,
                "objeto_ocorrencia": auditoria.objeto_ocorrencia,
                "registro_ocorrencia": auditoria.registro_ocorrencia,
                "data_hora_ocorrencia": auditoria.data_hora_ocorrencia
            }
            for auditoria in auditorias
        ]

    finally:
        db.close()