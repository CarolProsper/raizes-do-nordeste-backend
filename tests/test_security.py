
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import criar_token_acesso
from app.routers import auditorias, pagamentos


client = TestClient(app)


class ConsultaFalsa:
    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
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

    def rollback(self):
        pass


def criar_token(perfil):
    return criar_token_acesso(
        id_usuario=999,
        login="usuario_teste",
        perfil=perfil,
    )


def test_06_sem_token_nao_consulta_auditorias():
    resposta = client.get("/auditorias")

    assert resposta.status_code == 401


def test_07_atendente_nao_consulta_auditorias(monkeypatch):
    token = criar_token("Atendente")

    resposta = client.get(
        "/auditorias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 403


def test_08_gerente_consulta_auditorias(monkeypatch):
    monkeypatch.setattr(auditorias, "SessionLocal", SessaoFalsa)
    token = criar_token("Gerente_administrador")

    resposta = client.get(
        "/auditorias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_09_atendente_consulta_pagamentos(monkeypatch):
    monkeypatch.setattr(pagamentos, "SessionLocal", SessaoFalsa)
    token = criar_token("Atendente")

    resposta = client.get(
        "/pagamentos",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_10_atendente_nao_paga_pedido_inexistente(monkeypatch):
    monkeypatch.setattr(pagamentos, "SessionLocal", SessaoFalsa)
    token = criar_token("Atendente")

    resposta = client.post(
        "/pagamentos",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id_pedido": 999999,
            "forma_pagamento": "Pix",
            "status_pagamento": "Pendente",
            "data_hora_pagamento": "2026-10-09T12:00:00",
        },
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pedido não encontrado"
