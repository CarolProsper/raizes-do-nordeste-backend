
from fastapi import APIRouter, Depends, HTTPException, status
from app.database.database import SessionLocal
from app.database.models import Usuario
from app.schemas.usuario import UsuarioCreate
from app.core.security import criar_hash_senha
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_usuario(
    dados: UsuarioCreate,
    usuario_atual=Depends(exigir_perfil("Gerente_administrador"))
):
    perfis_permitidos = [
        "Gerente_administrador",
        "Atendente",
        "Cozinha",
        "Cliente"
    ]

    if dados.perfil not in perfis_permitidos:
        raise HTTPException(
            status_code=400,
            detail="Perfil inválido"
        )

    db = SessionLocal()

    try:
        existente = db.query(Usuario).filter(
            Usuario.login == dados.login
        ).first()

        if existente:
            raise HTTPException(
                status_code=409,
                detail="Login já cadastrado"
            )

        novo_usuario = Usuario(
            nome=dados.nome,
            login=dados.login,
            senha_hash=criar_hash_senha(dados.senha),
            perfil=dados.perfil,
            ativo=True
        )

        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

        return {
            "id_usuario": novo_usuario.id_usuario,
            "nome": novo_usuario.nome,
            "login": novo_usuario.login,
            "perfil": novo_usuario.perfil,
            "ativo": novo_usuario.ativo
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
