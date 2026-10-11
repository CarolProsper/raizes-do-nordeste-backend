from fastapi.testclient import TestClient
from app.main import app
from app.core.security import criar_token_acesso
from app.routers import pagamentos, item_pedido, pedidos


client = TestClient(app)


class ConsultaFalsa:
    def __init__(self, resultado=None, quantidade=0):
        self.resultado = resultado
        self.quantidade = quantidade

    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
        return self

    def first(self):
        return self.resultado

    def count(self):
        return self.quantidade

    def all(self):
        return []


class SessaoFalsa:
    def __init__(self, resultados=None, contagens=None):
        self.resultados = list(resultados or [])
        self.contagens = list(contagens or [])

    def query(self, *args, **kwargs):
        resultado = (
            self.resultados.pop(0)
            if self.resultados else None
        )
        quantidade = (
            self.contagens.pop(0)
            if self.contagens else 0
        )
        return ConsultaFalsa(resultado, quantidade)

    def close(self):
        pass

    def rollback(self):
        pass


def token_atendente():
    token = criar_token_acesso(
        id_usuario=999,
        login="atendente_teste",
        perfil="Atendente",
    )
    return {"Authorization": f"Bearer {token}"}


def test_11_pagamento_pedido_inexistente(monkeypatch):
    monkeypatch.setattr(
        pagamentos, "SessionLocal",
        lambda: SessaoFalsa()
    )

    resposta = client.post(
        "/pagamentos",
        headers=token_atendente(),
        json={
            "id_pedido": 999999,
            "forma_pagamento": "Pix",
            "status_pagamento": "Pendente",
            "data_hora_pagamento": "2026-10-09T12:00:00",
        },
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pedido não encontrado"


def test_12_pagamento_pedido_cancelado(monkeypatch):
    pedido_falso = type(
        "PedidoFalso", (),
        {"status": "Cancelado"}
    )()

    monkeypatch.setattr(
        pagamentos, "SessionLocal",
        lambda: SessaoFalsa(resultados=[pedido_falso])
    )

    resposta = client.post(
        "/pagamentos",
        headers=token_atendente(),
        json={
            "id_pedido": 123,
            "forma_pagamento": "Pix",
            "status_pagamento": "Pendente",
            "data_hora_pagamento": "2026-10-09T12:00:00",
        },
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == (
        "Não é possível pagar um pedido cancelado"
    )


def test_13_pagamento_pedido_sem_itens(monkeypatch):
    pedido_falso = type(
        "PedidoFalso", (),
        {"status": "Recebido"}
    )()

    monkeypatch.setattr(
        pagamentos, "SessionLocal",
        lambda: SessaoFalsa(
            resultados=[pedido_falso, None],
            contagens=[0, 0],
        )
    )

    resposta = client.post(
        "/pagamentos",
        headers=token_atendente(),
        json={
            "id_pedido": 123,
            "forma_pagamento": "Pix",
            "status_pagamento": "Pendente",
            "data_hora_pagamento": "2026-10-09T12:00:00",
        },
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == (
        "Não é possível pagar um pedido sem itens"
    )


def test_14_item_com_estoque_insuficiente(monkeypatch):
    pedido_falso = type(
        "PedidoFalso", (),
        {"status": "Aguardando Pagamento", "id_unidade": 1}
    )()
    produto_falso = type(
        "ProdutoFalso", (),
        {"preco_unitario": 10.0}
    )()
    estoque_falso = type(
        "EstoqueFalso", (),
        {"disponivel": True, "quantidade": 1}
    )()

    monkeypatch.setattr(
        item_pedido, "SessionLocal",
        lambda: SessaoFalsa(
            resultados=[pedido_falso, produto_falso, estoque_falso]
        )
    )

    resposta = client.post(
        "/item_pedido",
        headers=token_atendente(),
        json={
            "id_pedido": 123,
            "id_produto": 1,
            "quantidade": 5,
        },
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Estoque insuficiente"


def test_23_item_com_quantidade_invalida():
    for quantidade in [0, -1]:
        resposta = client.post(
            "/item_pedido",
            headers=token_atendente(),
            json={
                "id_pedido": 123,
                "id_produto": 1,
                "quantidade": quantidade,
            },
        )

        assert resposta.status_code == 422


def test_15_idempotencia_reutiliza_pedido(monkeypatch):
    pedido_existente = type(
        "PedidoFalso", (),
        {
            "numero": 42,
            "id_cliente": 1,
            "id_unidade": 1,
            "canal_pedido": "Balcão",
            "status": "Aguardando Pagamento",
            "data_hora_pedido": "2026-10-09T12:00:00",
            "motivo_cancelamento": None,
        }
    )()

    monkeypatch.setattr(
        pedidos, "SessionLocal",
        lambda: SessaoFalsa(resultados=[pedido_existente])
    )

    resposta = client.post(
        "/pedidos",
        headers={**token_atendente(), "idempotency-key": "teste-chave-123"},
        json={
            "id_cliente": 1,
            "id_unidade": 1,
            "canal_pedido": "Balcão",
            "status": "Recebido",
            "data_hora_pedido": "2026-10-09T12:00:00",
            "motivo_cancelamento": None,
        },
    )

    print("STATUS:", resposta.status_code)
    print("RESPOSTA:", resposta.json())

    assert resposta.status_code == 201
    assert resposta.json()["numero"] == 42

def test_16_pedido_novo_aguarda_pagamento(monkeypatch):
    from datetime import datetime

    cliente_falso = object()
    unidade_falsa = object()
    produto_falso = type(
        "ProdutoFalso", (),
        {"id_produto": 1, "preco_unitario": 10.0}
    )()
    estoque_falso = type(
        "EstoqueFalso", (),
        {"disponivel": True, "quantidade": 5}
    )()

    class ConsultaFalsa:
        def __init__(self, resultado):
            self.resultado = resultado

        def filter(self, *args, **kwargs):
            return self

        def with_for_update(self):
            return self

        def first(self):
            return self.resultado

    class BancoFalso:
        def __init__(self):
            self.resultados = iter([
                None,
                cliente_falso,
                unidade_falsa,
                produto_falso,
                estoque_falso
            ])
            self.novo_pedido = None
            self.itens = []

        def query(self, *args, **kwargs):
            return ConsultaFalsa(next(self.resultados))

        def add(self, objeto):
            if isinstance(objeto, pedidos.Pedido):
                self.novo_pedido = objeto
            else:
                self.itens.append(objeto)

        def flush(self):
            self.novo_pedido.numero = 43

        def commit(self):
            pass

        def refresh(self, objeto):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    banco = BancoFalso()
    monkeypatch.setattr(pedidos, "SessionLocal", lambda: banco)

    resposta = client.post(
        "/pedidos",
        headers={
            **token_atendente(),
            "idempotency-key": "teste-pedido-novo-456"
        },
        json={
            "id_cliente": 1,
            "id_unidade": 1,
            "canal_pedido": "Balcão",
            "status": "Recebido",
            "data_hora_pedido": datetime.now().isoformat(),
            "motivo_cancelamento": None,
            "itens": [{"id_produto": 1, "quantidade": 2}]
        }
    )

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "Aguardando Pagamento"
    assert len(banco.itens) == 1
    assert estoque_falso.quantidade == 3


def test_17_pagamento_pendente_mantem_pedido_aguardando(monkeypatch):
    pedido_falso = type(
        "PedidoFalso", (),
        {
            "numero": 123,
            "status": "Aguardando Pagamento",
        }
    )()

    class BancoFalso:
        def __init__(self):
            self.resultados = [pedido_falso, None, None]
            self.contagens = [0, 1, 0]
            self.pagamento = None

        def query(self, *args, **kwargs):
            resultado = (
                self.resultados.pop(0)
                if self.resultados else None
            )
            quantidade = (
                self.contagens.pop(0)
                if self.contagens else 0
            )

            return ConsultaFalsa(resultado, quantidade)

        def add(self, objeto):
            self.pagamento = objeto

        def commit(self):
            self.pagamento.id_pagamento = 50

        def refresh(self, objeto):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    banco = BancoFalso()

    monkeypatch.setattr(
        pagamentos, "SessionLocal", lambda: banco
    )

    resposta = client.post(
        "/pagamentos",
        headers=token_atendente(),
        json={
            "id_pedido": 123,
            "forma_pagamento": "Pix",
            "data_hora_pagamento": "2026-10-09T12:00:00",
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["status_pagamento"] == "Pendente"
    assert pedido_falso.status == "Aguardando Pagamento"


def test_24_impedir_segundo_pagamento_pendente(monkeypatch):
    pedido_falso = type(
        "PedidoFalso", (),
        {
            "numero": 123,
            "status": "Aguardando Pagamento",
        }
    )()

    banco = SessaoFalsa(
        resultados=[pedido_falso, None, None, object()],
        contagens=[0, 1, 0, 0],
    )

    monkeypatch.setattr(
        pagamentos, "SessionLocal", lambda: banco
    )

    resposta = client.post(
        "/pagamentos",
        headers=token_atendente(),
        json={
            "id_pedido": 123,
            "forma_pagamento": "Pix",
            "data_hora_pagamento": "2026-10-09T12:00:00",
        },
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == (
        "O pedido já possui um pagamento pendente"
    )


def test_18_cancelar_pedido_inexistente(monkeypatch):
    monkeypatch.setattr(
        pedidos, "SessionLocal",
        lambda: SessaoFalsa()
    )

    resposta = client.patch(
        "/pedidos/999999/cancelar",
        headers={
            "Authorization": f"Bearer {criar_token_acesso(id_usuario=1, login='admin_teste', perfil='Gerente_administrador')}"
        },
        params={"motivo": "Pedido de teste"}
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pedido não encontrado"


def test_19_cancelar_pedido_com_pagamento_autorizado(monkeypatch):
    pedido_falso = type(
        "PedidoFalso",
        (),
        {
            "numero": 123,
            "status": "Aguardando Pagamento",
            "id_unidade": 1,
            "motivo_cancelamento": None,
        },
    )()

    pagamento_falso = type("PagamentoFalso", (), {})()

    monkeypatch.setattr(
        pedidos,
        "SessionLocal",
        lambda: SessaoFalsa(
            resultados=[pedido_falso, pagamento_falso]
        ),
    )

    token = criar_token_acesso(
        id_usuario=1,
        login="admin_teste",
        perfil="Gerente_administrador",
    )

    resposta = client.patch(
        "/pedidos/123/cancelar",
        headers={"Authorization": f"Bearer {token}"},
        params={"motivo": "Teste de cancelamento"},
    )

    assert resposta.status_code == 409
    assert "pagamento autorizado" in resposta.json()["detail"]


def test_20_cancelar_pedido_devolve_estoque(monkeypatch):
    pedido_falso = type(
        "PedidoFalso",
        (),
        {
            "numero": 123,
            "status": "Aguardando Pagamento",
            "id_unidade": 1,
            "motivo_cancelamento": None,
        },
    )()

    item_falso = type(
        "ItemFalso",
        (),
        {
            "id_produto": 10,
            "quantidade": 3,
        },
    )()

    estoque_falso = type(
        "EstoqueFalso",
        (),
        {
            "quantidade": 5,
        },
    )()

    class BancoFalso:
        def __init__(self):
            self.resultados = [
                pedido_falso,
                None,
                [item_falso],
                estoque_falso,
            ]

        def query(self, *args, **kwargs):
            resultado = (
                self.resultados.pop(0)
                if self.resultados else None
            )
            return ConsultaCancelamento(resultado)

        def commit(self):
            pass

        def refresh(self, objeto):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    class ConsultaCancelamento:
        def __init__(self, resultado):
            self.resultado = resultado

        def filter(self, *args, **kwargs):
            return self

        def with_for_update(self):
            return self

        def first(self):
            return self.resultado

        def all(self):
            return self.resultado or []

    banco = BancoFalso()

    monkeypatch.setattr(
        pedidos,
        "SessionLocal",
        lambda: banco,
    )

    token = criar_token_acesso(
        id_usuario=1,
        login="admin_teste",
        perfil="Gerente_administrador",
    )

    resposta = client.patch(
        "/pedidos/123/cancelar",
        headers={"Authorization": f"Bearer {token}"},
        params={"motivo": "Cancelamento de teste"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "Cancelado"
    assert estoque_falso.quantidade == 8
    assert pedido_falso.motivo_cancelamento == "Cancelamento de teste"


def test_21_cancelar_pedido_sem_motivo(monkeypatch):
    token = criar_token_acesso(
        id_usuario=1,
        login="admin_teste",
        perfil="Gerente_administrador",
    )

    resposta = client.patch(
        "/pedidos/123/cancelar",
        headers={"Authorization": f"Bearer {token}"},
        params={"motivo": "   "},
    )

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == (
        "O motivo do cancelamento é obrigatório"
    )


def test_22_idempotencia_conflito_integridade(monkeypatch):
    pedido_existente = type(
        "PedidoFalso", (),
        {
            "numero": 42,
            "id_cliente": 99,
            "id_unidade": 1,
            "canal_pedido": "Balcão",
            "status": "Aguardando Pagamento",
            "data_hora_pedido": "2026-10-09T12:00:00",
            "motivo_cancelamento": None,
        },
    )()

    monkeypatch.setattr(
        pedidos,
        "SessionLocal",
        lambda: SessaoFalsa(resultados=[pedido_existente])
    )

    resposta = client.post(
        "/pedidos",
        headers={
            **token_atendente(),
            "idempotency-key": "teste-conflito-22"
        },
        json={
            "id_cliente": 1,
            "id_unidade": 1,
            "canal_pedido": "Balcão",
            "status": "Recebido",
            "data_hora_pedido": "2026-10-09T12:00:00",
            "motivo_cancelamento": None,
            "itens": [{"id_produto": 1, "quantidade": 1}],
        },
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == (
        "Chave de idempotência já utilizada em outro pedido"
    )


def test_26_pagamento_autorizado_atualiza_pedido(monkeypatch):
    pagamento = type(
        "PagamentoFalso", (),
        {
            "id_pagamento": 1,
            "id_pedido": 123,
            "status_pagamento": "Pendente",
        }
    )()

    pedido = type(
        "PedidoFalso", (),
        {
            "numero": 123,
            "status": "Aguardando Pagamento",
        }
    )()

    banco = SessaoFalsa(resultados=[pagamento, pedido])
    banco.commit = lambda: None
    banco.refresh = lambda objeto: None

    monkeypatch.setattr(
        pagamentos, "SessionLocal", lambda: banco
    )

    resposta = client.post(
        "/pagamentos/1/resultado",
        headers=token_atendente(),
        json={"resultado": "Autorizado"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["status_pagamento"] == "Autorizado"
    assert resposta.json()["status_pedido"] == "Em Preparação"


def test_27_pagamento_recusado_mantem_pedido_aguardando(monkeypatch):
    pagamento = type(
        "PagamentoFalso", (),
        {
            "id_pagamento": 2,
            "id_pedido": 123,
            "status_pagamento": "Pendente",
        }
    )()

    pedido = type(
        "PedidoFalso", (),
        {
            "numero": 123,
            "status": "Aguardando Pagamento",
        }
    )()

    banco = SessaoFalsa(resultados=[pagamento, pedido])
    banco.commit = lambda: None
    banco.refresh = lambda objeto: None

    monkeypatch.setattr(
        pagamentos, "SessionLocal", lambda: banco
    )

    resposta = client.post(
        "/pagamentos/2/resultado",
        headers=token_atendente(),
        json={"resultado": "Recusado"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["status_pagamento"] == "Recusado"
    assert resposta.json()["status_pedido"] == "Aguardando Pagamento"



def test_28_cliente_consulta_somente_seus_pedidos(monkeypatch):
    pedido_proprio = type("PedidoFalso", (), {
        "numero": 12,
        "id_unidade": 1,
        "canal_pedido": "App",
        "status": "Aguardando Pagamento",
        "data_hora_pedido": "2026-10-11T12:00:00",
    })()

    class ConsultaPedidos:
        def __init__(self):
            self.filtro_aplicado = False

        def filter(self, *condicoes, **kwargs):
            # Verifica se a consulta possui uma condição de filtro.
            assert condicoes
            self.filtro_aplicado = True
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            assert self.filtro_aplicado
            return [pedido_proprio]

    consulta = ConsultaPedidos()

    class BancoFalso:
        def query(self, modelo):
            assert modelo is pedidos.Pedido
            return consulta

        def close(self):
            pass

    monkeypatch.setattr(
        pedidos, "SessionLocal", lambda: BancoFalso()
    )

    token = criar_token_acesso(
        id_usuario=4,
        login="cliente_teste",
        perfil="Cliente",
        id_cliente=2,
    )

    resposta = client.get(
        "/pedidos/meus",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 200
    assert [p["numero"] for p in resposta.json()] == [12]

def test_29_cliente_sem_vinculo_nao_consulta_pedidos():
    token = criar_token_acesso(
        id_usuario=999,
        login="cliente_sem_vinculo",
        perfil="Cliente",
    )

    resposta = client.get(
        "/pedidos/meus",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == (
        "Usuário não está vinculado a um cliente"
    )

def test_30_cliente_nao_consulta_itens_de_pedido_alheio(monkeypatch):
    class ConsultaPedido:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            # Pedido inexistente para o cliente autenticado.
            return None

    class BancoFalso:
        def query(self, modelo):
            assert modelo is item_pedido.Pedido
            return ConsultaPedido()

        def close(self):
            pass

    monkeypatch.setattr(
        item_pedido, "SessionLocal", lambda: BancoFalso()
    )

    token = criar_token_acesso(
        id_usuario=4,
        login="cliente_teste",
        perfil="Cliente",
        id_cliente=2,
    )

    resposta = client.get(
        "/item_pedido/meu/8",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pedido não encontrado"

def test_31_cliente_nao_paga_pedido_de_outro_cliente(monkeypatch):
    pedido_alheio = type("PedidoFalso", (), {
        "numero": 8,
        "id_cliente": 5,
        "status": "Aguardando Pagamento",
    })()

    class ConsultaFalsaPagamento:
        def filter(self, *args, **kwargs):
            return self

        def with_for_update(self):
            return self

        def first(self):
            return pedido_alheio

    class BancoFalsoPagamento:
        def query(self, modelo):
            assert modelo is pagamentos.Pedido
            return ConsultaFalsaPagamento()

        def close(self):
            pass

        def rollback(self):
            pass

    monkeypatch.setattr(
        pagamentos,
        "SessionLocal",
        lambda: BancoFalsoPagamento(),
    )

    token = criar_token_acesso(
        id_usuario=4,
        login="cliente_teste",
        perfil="Cliente",
        id_cliente=2,
    )

    resposta = client.post(
        "/pagamentos",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id_pedido": 8,
            "forma_pagamento": "Pix",
            "data_hora_pagamento": "2026-10-11T12:00:00",
        },
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pedido não encontrado"

def test_32_cliente_nao_acessa_rotas_de_operacao_interna():
    token = criar_token_acesso(
        id_usuario=4,
        login="cliente_teste",
        perfil="Cliente",
        id_cliente=2,
    )
    headers = {"Authorization": f"Bearer {token}"}

    respostas = [
        client.patch(
            "/pedidos/8/status",
            params={"novo_status": "Pronto"},
            headers=headers,
        ),
        client.patch(
            "/pedidos/8/cancelar",
            params={"motivo": "Teste"},
            headers=headers,
        ),
        client.post(
            "/pagamentos/1/resultado",
            json={"resultado": "Autorizado"},
            headers=headers,
        ),
    ]

    assert [r.status_code for r in respostas] == [403, 403, 403]


def test_33_cozinha_pode_marcar_pedido_como_pronto(monkeypatch):
    pedido = type(
        "PedidoFalso", (),
        {"numero": 10, "status": "Em Preparação"}
    )()

    class BancoFalso(SessaoFalsa):
        def commit(self):
            pass

        def refresh(self, objeto):
            pass

    monkeypatch.setattr(
        pedidos, "SessionLocal",
        lambda: BancoFalso(resultados=[pedido])
    )

    token = criar_token_acesso(
        id_usuario=10,
        login="cozinha_teste",
        perfil="Cozinha",
    )

    resposta = client.patch(
        "/pedidos/10/status",
        params={"novo_status": "Pronto"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "Pronto"


def test_34_cozinha_nao_pode_entregar_pedido(monkeypatch):
    pedido = type(
        "PedidoFalso", (),
        {"numero": 10, "status": "Pronto"}
    )()

    monkeypatch.setattr(
        pedidos, "SessionLocal",
        lambda: SessaoFalsa(resultados=[pedido])
    )

    token = criar_token_acesso(
        id_usuario=10,
        login="cozinha_teste",
        perfil="Cozinha",
    )

    resposta = client.patch(
        "/pedidos/10/status",
        params={"novo_status": "Entregue"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 403