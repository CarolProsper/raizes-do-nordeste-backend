from app.database.database import engine, Base
from app.database.models import Cliente


print("Criando tabelas...")

Base.metadata.create_all(bind=engine)

print("Tabelas criadas com sucesso!")