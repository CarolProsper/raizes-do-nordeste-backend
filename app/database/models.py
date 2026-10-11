from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, Integer, String, ForeignKey, UniqueConstraint, CheckConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id_cliente: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    cpf: Mapped[str | None] = mapped_column(
        String(11),
        unique=True,
        nullable=True
    )

    data_nascimento: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    telefone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    autoriza_email: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    autoriza_telefone: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

class Unidade(Base):
    __tablename__ = "unidade"

    id_unidade: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    endereco: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    cidade: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(2),
        nullable=False
    )

class Produto(Base):
    __tablename__ = "produto"

    id_produto: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    preco_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

class Pedido(Base):
    __tablename__ = "pedido"

    __table_args__ = (
        CheckConstraint(
            "(status = 'Cancelado' AND motivo_cancelamento IS NOT NULL) "
            "OR "
            "(status <> 'Cancelado' AND motivo_cancelamento IS NULL)",
            name="pedido_cancelamento_check"
        ),
    )

    numero: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_cliente: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cliente.id_cliente"),
        nullable=False
    )

    id_unidade: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("unidade.id_unidade"),
        nullable=False
    )

    canal_pedido: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    data_hora_pedido: Mapped[datetime] = mapped_column(
        nullable=False
    )

    motivo_cancelamento: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    chave_idempotencia: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )
class ItemPedido(Base):
    __tablename__ = "item_pedido"

    id_item_pedido: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_pedido: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pedido.numero"),
        nullable=False
    )

    id_produto: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("produto.id_produto"),
        nullable=False
    )

    quantidade: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    preco_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

class Estoque(Base):
    __tablename__ = "estoque"


    __table_args__ = (
        UniqueConstraint(
            "id_unidade",
            "id_produto",
            name="estoque_unidade_produto_unique"
        ),
        CheckConstraint(
            "quantidade >= 0",
            name="estoque_quantidade_nao_negativa"
        ),
    )


    id_estoque: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_unidade: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("unidade.id_unidade"),
        nullable=False
    )

    id_produto: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("produto.id_produto"),
        nullable=False
    )

    quantidade: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    disponivel: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

class Pagamento(Base):
    __tablename__ = "pagamento"

    id_pagamento: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_pedido: Mapped[int] = mapped_column(
    Integer,
    ForeignKey("pedido.numero"),
    nullable=False
    )

    forma_pagamento: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    status_pagamento: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )


    data_hora_pagamento: Mapped[datetime] = mapped_column(
        default=datetime.now,
        nullable=False
    )


class Fidelidade(Base):
    __tablename__ = "fidelidade"

    id_fidelidade: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_cliente: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cliente.id_cliente"),
        nullable=False,
        unique=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    data_adesao: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False
    )

    data_exclusao: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

class MovimentacaoPontos(Base):
    __tablename__ = "movimentacao_pontos"

    id_mov_pontos: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_fidelidade: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fidelidade.id_fidelidade"),
        nullable=False
    )

    id_pedido: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("pedido.numero"),
        nullable=True
    )

    quantidade_pontos: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    tipo: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    origem_movimentacao: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    data_hora: Mapped[datetime] = mapped_column(
        default=datetime.now,
        nullable=False
    )

class Funcionario(Base):
    __tablename__ = "funcionario"

    id_funcionario: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_unidade: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("unidade.id_unidade"),
        nullable=False
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    funcao: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

class Auditoria(Base):
    __tablename__ = "auditoria"

    id_auditoria: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_funcionario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("funcionario.id_funcionario"),
        nullable=False
    )

    tipo_ocorrencia: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    objeto_ocorrencia: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    registro_ocorrencia: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    data_hora_ocorrencia: Mapped[datetime] = mapped_column(
        default=datetime.now,
        nullable=False
    )

class AlteracaoFuncao(Base):
    __tablename__ = "alteracao_funcao"

    id_alteracao_funcao: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_funcionario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("funcionario.id_funcionario"),
        nullable=False
    )

    funcao_anterior: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    funcao_nova: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    data_hora_alteracao: Mapped[datetime] = mapped_column(
        default=datetime.now,
        nullable=False
    )

class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    login: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True
    )

    senha_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    perfil: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    id_cliente: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("cliente.id_cliente"),
        nullable=True,
    )
