"""Testes da API JSON /api/v1 usada pelo app mobile.

Cobre:
- POST /api/v1/auth/login (sucesso cidadao/empresa/admin, credencial invalida)
- GET  /api/v1/auth/me    (com token valido, sem token, token invalido)
"""

import sqlite3
import os
import pytest


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    """Cria a aplicacao Flask apontada para um banco temporario, com o seed padrao."""
    tmp = tmp_path_factory.mktemp("db")
    db_path = str(tmp / "test_api_v1.db")
    _orig = sqlite3.connect

    import ecotech.infrastructure.persistence.dados as _dados_mod

    class _PatchedConnect:
        def __call__(self, path, **kwargs):
            return _orig(db_path, **kwargs)

    _dados_mod.sqlite3.connect = _PatchedConnect()

    os.environ.pop("WERKZEUG_RUN_MAIN", None)

    from ecotech.infrastructure.web import criar_app
    application = criar_app()
    application.config["TESTING"] = True
    application.config["SECRET_KEY"] = "test-secret-key-com-pelo-menos-32-bytes"

    yield application

    _dados_mod.sqlite3.connect = _orig


@pytest.fixture
def client(app):
    return app.test_client()


# Credenciais do seed padrao (_inicializar_dados_exemplo)
_CPF_CIDADAO = "12345678909"
_SENHA_CIDADAO = "cidadao123"
_CNPJ_EMPRESA = "11222333000181"
_SENHA_EMPRESA = "empresa123"
_EMAIL_ADMIN = "admin@ecotech.com"
_SENHA_ADMIN = "admin123"


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------

def test_login_cidadao_com_credenciais_validas(client):
    resp = client.post("/api/v1/auth/login", json={
        "tipo": "cidadao", "credencial": _CPF_CIDADAO, "senha": _SENHA_CIDADAO,
    })
    corpo = resp.get_json()
    assert resp.status_code == 200
    assert corpo["token_type"] == "Bearer"
    assert corpo["access_token"]
    assert corpo["usuario"]["tipo"] == "cidadao"


def test_login_aceita_cpf_formatado_com_pontuacao(client):
    resp = client.post("/api/v1/auth/login", json={
        "tipo": "cidadao", "credencial": "123.456.789-09", "senha": _SENHA_CIDADAO,
    })
    assert resp.status_code == 200


def test_login_empresa_com_credenciais_validas(client):
    resp = client.post("/api/v1/auth/login", json={
        "tipo": "empresa", "credencial": _CNPJ_EMPRESA, "senha": _SENHA_EMPRESA,
    })
    corpo = resp.get_json()
    assert resp.status_code == 200
    assert corpo["usuario"]["tipo"] == "empresa"


def test_login_admin_com_credenciais_validas(client):
    resp = client.post("/api/v1/auth/login", json={
        "tipo": "administrador", "credencial": _EMAIL_ADMIN, "senha": _SENHA_ADMIN,
    })
    corpo = resp.get_json()
    assert resp.status_code == 200
    assert corpo["usuario"]["tipo"] == "administrador"


def test_login_senha_incorreta_retorna_401(client):
    resp = client.post("/api/v1/auth/login", json={
        "tipo": "cidadao", "credencial": _CPF_CIDADAO, "senha": "senha-errada",
    })
    assert resp.status_code == 401
    assert "erro" in resp.get_json()


def test_login_sem_corpo_json_retorna_401(client):
    resp = client.post("/api/v1/auth/login")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------

def _obter_token(client, tipo, credencial, senha):
    resp = client.post("/api/v1/auth/login", json={
        "tipo": tipo, "credencial": credencial, "senha": senha,
    })
    return resp.get_json()["access_token"]


def test_me_sem_token_retorna_401(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_com_token_invalido_retorna_401(client):
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token-invalido"})
    assert resp.status_code == 401


def test_me_com_token_valido_retorna_dados_do_usuario(client):
    token = _obter_token(client, "cidadao", _CPF_CIDADAO, _SENHA_CIDADAO)
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    corpo = resp.get_json()
    assert resp.status_code == 200
    assert corpo["tipo"] == "cidadao"
    assert corpo["email"]


# ---------------------------------------------------------------------------
# POST /api/v1/auth/registrar
# ---------------------------------------------------------------------------

def test_registrar_cidadao_com_dados_validos(client):
    resp = client.post("/api/v1/auth/registrar", json={
        "tipo": "cidadao", "nome": "Nova Pessoa", "email": "nova.pessoa@example.com",
        "senha": "senha123", "senha_confirmacao": "senha123", "cpf": "52998224725",
    })
    corpo = resp.get_json()
    assert resp.status_code == 200
    assert corpo["usuario"]["tipo"] == "cidadao"
    assert corpo["access_token"]


def test_registrar_senhas_diferentes_retorna_400(client):
    resp = client.post("/api/v1/auth/registrar", json={
        "tipo": "cidadao", "nome": "Fulano", "email": "fulano@example.com",
        "senha": "senha123", "senha_confirmacao": "outra-senha", "cpf": "11144477735",
    })
    assert resp.status_code == 400


def test_registrar_senha_curta_retorna_400(client):
    resp = client.post("/api/v1/auth/registrar", json={
        "tipo": "cidadao", "nome": "Fulano", "email": "fulano2@example.com",
        "senha": "123", "senha_confirmacao": "123", "cpf": "11144477735",
    })
    assert resp.status_code == 400


def test_registrar_cpf_invalido_retorna_400(client):
    resp = client.post("/api/v1/auth/registrar", json={
        "tipo": "cidadao", "nome": "Fulano", "email": "fulano3@example.com",
        "senha": "senha123", "senha_confirmacao": "senha123", "cpf": "00000000000",
    })
    assert resp.status_code == 400


def test_registrar_email_ja_cadastrado_retorna_400(client):
    resp = client.post("/api/v1/auth/registrar", json={
        "tipo": "cidadao", "nome": "Joao Duplicado", "email": "joao@ecotech.com",
        "senha": "senha123", "senha_confirmacao": "senha123", "cpf": "39053344705",
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# CORS, necessario para o app flutter web acessar a api de outra origem
# ---------------------------------------------------------------------------

def test_rota_api_libera_cors(client):
    resp = client.post("/api/v1/auth/login", json={
        "tipo": "cidadao", "credencial": _CPF_CIDADAO, "senha": _SENHA_CIDADAO,
    })
    assert resp.headers["Access-Control-Allow-Origin"] == "*"


def test_rota_html_nao_libera_cors(client):
    resp = client.get("/login")
    assert "Access-Control-Allow-Origin" not in resp.headers

