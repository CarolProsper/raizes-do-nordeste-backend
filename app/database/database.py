from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_user = os.getenv("POSTGRES_USER", "raizes_user")
db_password = quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
db_host = os.getenv("POSTGRES_HOST", "localhost")
db_port = os.getenv("POSTGRES_PORT", "5432")
db_name = os.getenv("POSTGRES_DB", "raizes_nordeste")

if not db_password:
    raise RuntimeError("Configure POSTGRES_PASSWORD no arquivo .env")

DATABASE_URL = (
    f"postgresql+psycopg2://{db_user}:{db_password}"
    f"@{db_host}:{db_port}/{db_name}"
)


engine = create_engine(
    DATABASE_URL,
    echo=True
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()