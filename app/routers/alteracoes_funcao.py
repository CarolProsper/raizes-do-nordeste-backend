from fastapi import APIRouter, status, HTTPException, Depends
from app.database.database import SessionLocal
from app.database.models import AlteracaoFuncao, Funcionario
from app.schemas.alteracao_funcao import AlteracaoFuncaoCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/alteracoes_funcao",
    tags=["Alterações de Função"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_alteracao_funcao(
    alteracao: AlteracaoFuncaoCreate,
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        # Verifica se o funcionário existe
        funcionario = db.query(Funcionario).filter(
            Funcionario.id_funcionario == alteracao.id_funcionario
        ).first()

        if funcionario is None:
            raise HTTPException(
                status_code=404,
                detail="Funcionário não encontrado"
            )

        # Guarda a função atual antes da alteração
        funcao_anterior = funcionario.funcao

        # Atualiza a função atual do funcionário
        funcionario.funcao = alteracao.funcao_nova

        # Registra o histórico da alteração
        nova_alteracao = AlteracaoFuncao(
            id_funcionario=funcionario.id_funcionario,
            funcao_anterior=funcao_anterior,
            funcao_nova=alteracao.funcao_nova,
        )

        db.add(nova_alteracao)
        db.commit()
        db.refresh(nova_alteracao)

        return {
            "id_alteracao_funcao": nova_alteracao.id_alteracao_funcao,
            "id_funcionario": funcionario.id_funcionario,
            "funcao_anterior": funcao_anterior,
            "funcao_nova": funcionario.funcao,
            "data_hora_alteracao": nova_alteracao.data_hora_alteracao
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
def listar_alteracoes_funcao(
    usuario=Depends(exigir_perfil("Gerente_administrador"))
):
    db = SessionLocal()

    try:
        alteracoes = db.query(AlteracaoFuncao).all()

        return [
            {
                "id_alteracao_funcao": alteracao.id_alteracao_funcao,
                "id_funcionario": alteracao.id_funcionario,
                "funcao_anterior": alteracao.funcao_anterior,
                "funcao_nova": alteracao.funcao_nova,
                "data_hora_alteracao": alteracao.data_hora_alteracao
            }
            for alteracao in alteracoes
        ]

    finally:
        db.close()