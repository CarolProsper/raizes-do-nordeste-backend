from fastapi import APIRouter, status, Depends
from app.database.database import SessionLocal
from app.database.models import Cliente
from app.schemas.cliente import ClienteCreate
from app.core.auth import exigir_perfil

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_cliente(cliente: ClienteCreate):
    db = SessionLocal()

    try:
        novo_cliente = Cliente(
            nome=cliente.nome,
            cpf=cliente.cpf,
            data_nascimento=cliente.data_nascimento,
            telefone=cliente.telefone,
            email=cliente.email,
            autoriza_email=cliente.autoriza_email,
            autoriza_telefone=cliente.autoriza_telefone,
            status=cliente.status
        )

        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)

        return {
            "id_cliente": novo_cliente.id_cliente,
            "nome": novo_cliente.nome,
            "data_nascimento": novo_cliente.data_nascimento,
            "telefone": novo_cliente.telefone,
            "email": novo_cliente.email,
            "autoriza_email": novo_cliente.autoriza_email,
            "autoriza_telefone": novo_cliente.autoriza_telefone,
            "status": novo_cliente.status
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.get("")
def listar_clientes(
    usuario=Depends(
    exigir_perfil("Gerente_administrador", "Atendente")
)
):
    db = SessionLocal()

    try:
        clientes = db.query(Cliente).all()

        return [
            {
                "id_cliente": cliente.id_cliente,
                "nome": cliente.nome,
                "data_nascimento": cliente.data_nascimento,
                "telefone": cliente.telefone,
                "email": cliente.email,
                "autoriza_email": cliente.autoriza_email,
                "autoriza_telefone": cliente.autoriza_telefone,
                "status": cliente.status
            }
            for cliente in clientes
        ]

    finally:
        db.close()