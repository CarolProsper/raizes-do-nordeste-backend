
from fastapi.testclient import TestClient
from app.core.security import criar_token_acesso
from app.main import app
from app.routers import auth, produtos, unidades


client = TestClient(app)


# Simula consultas ao banco, sem alterar dados reais.
class ConsultaFalsa:
    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return []

    def first(self):
        return None


class SessaoFalsa:
    def query(self, *args, **kwargs):
        return ConsultaFalsa()

    def close(self):
        pass


def test_01_api_responde():
    resposta = client.get("/")

    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == (
        "API Raizes do Nordeste funcionando!"
    )


def test_02_rotas_estao_registradas():
    resposta = client.get("/openapi.json")

    assert resposta.status_code == 200

    caminhos = resposta.json()["paths"]

    rotas_esperadas = [
        "/auth/login",
        "/clientes",
        "/produtos",
        "/unidades",
        "/pedidos",
        "/item_pedido",
        "/pagamentos",
        "/estoque",
        "/funcionarios",
        "/auditorias",
        "/alteracoes_funcao",
        "/fidelidades",
        "/movimentacao_pontos",
        "/usuarios",
    ]

    for rota in rotas_esperadas:
        assert rota in caminhos, f"Rota ausente: {rota}"


def test_03_consultas_protegidas_sem_token():
    rotas = [
        "/clientes",
        "/estoque",
        "/fidelidades",
        "/funcionarios",
        "/item_pedido",
        "/movimentacao_pontos",
        "/pagamentos",
        "/pedidos",
        "/pedidos/1/total",
        "/auditorias",
        "/alteracoes_funcao",
    ]

    for rota in rotas:
        resposta = client.get(rota)

        assert resposta.status_code in (401, 403), (
            f"{rota} deveria exigir autenticação, "
            f"mas retornou {resposta.status_code}"
        )


def test_04_catalogo_publico():
    produtos.SessionLocal = SessaoFalsa
    unidades.SessionLocal = SessaoFalsa

    resposta_produtos = client.get("/produtos")
    resposta_unidades = client.get("/unidades")

    assert resposta_produtos.status_code == 200
    assert resposta_unidades.status_code == 200

    assert resposta_produtos.json() == []
    assert resposta_unidades.json() == []


def test_05_login_rejeita_credenciais_invalidas(monkeypatch):
    monkeypatch.setattr(auth, "SessionLocal", SessaoFalsa)

    resposta = client.post(
        "/auth/login",
        json={
            "login": "usuario_inexistente_teste",
            "senha": "SenhaInvalida123!",
        },
    )

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Login ou senha inválidos"


def test_25_produto_rejeita_preco_negativo():
    token = criar_token_acesso(
        id_usuario=1,
        login="admin_teste",
        perfil="Gerente_administrador",
    )

    resposta = client.post(
        "/produtos",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nome": "Produto Teste",
            "preco_unitario": "-10.00",
        },
    )

    assert resposta.status_code == 422
