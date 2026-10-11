from app.database.database import SessionLocal
from app.database.models import Usuario
import os
from dotenv import load_dotenv
from app.core.security import criar_hash_senha

load_dotenv()


db = SessionLocal()

try:
    usuario_existente = db.query(Usuario).filter(
        Usuario.login == "admin"
    ).first()

    if usuario_existente:
        print("Usuário admin já existe.")

    else:
        usuario = Usuario(
            nome="Administrador",
            login="admin",
            senha_hash=criar_hash_senha(os.environ["DEMO_USER_PASSWORD"]),
            perfil="Gerente_administrador",
            ativo=True
        )

        db.add(usuario)
        db.commit()

        print("Usuário admin criado com sucesso.")

finally:
    db.close()
