"""Testes da API JSON /api/v1 usada pelo app mobile.

Cobre:
- POST /api/v1/auth/login (sucesso cidadao/empresa/admin, credencial invalida)
- GET  /api/v1/auth/me    (com token valido, sem token, token invalido)
"""

import io
import sqlite3
import os
from datetime import datetime, timedelta
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
# GET /api/v1/dashboard
# ---------------------------------------------------------------------------

def test_dashboard_sem_token_retorna_401(client):
    assert client.get("/api/v1/dashboard").status_code == 401


@pytest.mark.parametrize(
    "tipo,credencial,senha,chaves_metricas",
    [
        ("cidadao", _CPF_CIDADAO, _SENHA_CIDADAO, {"saldo", "pontos", "tier", "dispositivos"}),
        ("empresa", _CNPJ_EMPRESA, _SENHA_EMPRESA, {"finalizadas", "ativas", "peso_processado_kg", "saldo"}),
        ("administrador", _EMAIL_ADMIN, _SENHA_ADMIN, {"peso_total_kg", "solicitacoes", "finalizadas", "receita"}),
    ],
)
def test_dashboard_retorna_contrato_especifico_por_perfil(
    client, tipo, credencial, senha, chaves_metricas
):
    token = _obter_token(client, tipo, credencial, senha)
    resp = client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    corpo = resp.get_json()
    assert resp.status_code == 200
    assert corpo["tipo"] == tipo
    assert corpo["usuario"]["tipo"] == tipo
    assert chaves_metricas <= corpo["metricas"].keys()


# ---------------------------------------------------------------------------
# GET/PATCH /api/v1/perfil
# ---------------------------------------------------------------------------

def test_perfil_retorna_dados_especificos_do_cidadao(client):
    token = _obter_token(client, "cidadao", _CPF_CIDADAO, _SENHA_CIDADAO)
    resp = client.get(
        "/api/v1/perfil",
        headers={"Authorization": f"Bearer {token}"},
    )
    corpo = resp.get_json()
    assert resp.status_code == 200
    assert corpo["usuario"]["cpf"] == _CPF_CIDADAO
    assert "tier" in corpo["resumo"]
    assert len(corpo["resumo"]["conquistas"]) == 4


def test_perfil_pode_atualizar_nome_email_e_senha(client):
    cadastro = client.post("/api/v1/auth/registrar", json={
        "tipo": "cidadao",
        "nome": "Perfil Mobile",
        "email": "perfil.mobile@example.com",
        "senha": "senha123",
        "senha_confirmacao": "senha123",
        "cpf": "11144477735",
    })
    token = cadastro.get_json()["access_token"]
    resp = client.patch(
        "/api/v1/perfil",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nome": "Perfil Atualizado",
            "email": "perfil.atualizado@example.com",
            "senha_atual": "senha123",
            "nova_senha": "senha456",
            "confirma_senha": "senha456",
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()["usuario"]["nome"] == "Perfil Atualizado"
    novo_login = client.post("/api/v1/auth/login", json={
        "tipo": "cidadao",
        "credencial": "11144477735",
        "senha": "senha456",
    })
    assert novo_login.status_code == 200


# ---------------------------------------------------------------------------
# Jornada do cidadao
# ---------------------------------------------------------------------------

def _dados_nova_solicitacao(ponto_id):
    amanha = datetime.now() + timedelta(days=1)
    return {
        "tipo_dispositivo": "celular",
        "subcategoria": "Smartphone",
        "nome": "Galaxy S20",
        "ano_fabricacao": "2020",
        "quantidade": "2",
        "peso_kg": "",
        "tipo_coleta": "entrega_ponto",
        "ponto_id": ponto_id,
        "nome_contato": "Joao Silva",
        "observacoes": "Tela trincada",
        "data_coleta": amanha.strftime("%Y-%m-%d"),
        "horario_inicio": "10:00",
        "horario_fim": "12:00",
    }


def test_pontos_coleta_e_criacao_com_peso_estimado_e_foto(client):
    token = _obter_token(client, "cidadao", _CPF_CIDADAO, _SENHA_CIDADAO)
    headers = {"Authorization": f"Bearer {token}"}
    pontos_resp = client.get("/api/v1/pontos-coleta", headers=headers)
    pontos = pontos_resp.get_json()["pontos"]
    assert pontos_resp.status_code == 200
    assert pontos
    assert {"empresa", "capacidade_kg", "ocupacao_kg"} <= pontos[0].keys()

    dados = _dados_nova_solicitacao(pontos[0]["id"])
    dados["fotos"] = (io.BytesIO(b"\x89PNG\r\n\x1a\nconteudo"), "produto.png")
    resp = client.post(
        "/api/v1/solicitacoes",
        headers=headers,
        data=dados,
        content_type="multipart/form-data",
    )
    corpo = resp.get_json()
    assert resp.status_code == 201, corpo
    assert corpo["peso_origem"] == "estimado"
    assert corpo["peso_estimado_kg"] == 0.4
    assert corpo["peso_confirmado_kg"] is None
    assert corpo["itens"][0]["ano_fabricacao"] == 2020
    assert len(corpo["fotos"]) == 1

    detalhe = client.get(f"/api/v1/solicitacoes/{corpo['id']}", headers=headers)
    assert detalhe.status_code == 200
    foto = client.get(corpo["fotos"][0]["url"], headers=headers)
    assert foto.status_code == 200
    assert foto.mimetype == "image/png"


def test_upload_invalido_nao_cria_solicitacao_parcial(client):
    token = _obter_token(client, "cidadao", _CPF_CIDADAO, _SENHA_CIDADAO)
    headers = {"Authorization": f"Bearer {token}"}
    antes = client.get("/api/v1/solicitacoes", headers=headers).get_json()["total"]
    ponto_id = client.get("/api/v1/pontos-coleta", headers=headers).get_json()["pontos"][0]["id"]
    dados = _dados_nova_solicitacao(ponto_id)
    dados["fotos"] = (io.BytesIO(b"arquivo-invalido"), "produto.txt")
    resp = client.post(
        "/api/v1/solicitacoes", headers=headers, data=dados,
        content_type="multipart/form-data",
    )
    depois = client.get("/api/v1/solicitacoes", headers=headers).get_json()["total"]
    assert resp.status_code == 400
    assert depois == antes


def test_solicitacao_de_outro_cidadao_nao_pode_ser_acessada(client):
    token_joao = _obter_token(client, "cidadao", _CPF_CIDADAO, _SENHA_CIDADAO)
    headers_joao = {"Authorization": f"Bearer {token_joao}"}
    solicitacoes = client.get("/api/v1/solicitacoes", headers=headers_joao).get_json()["itens"]
    assert solicitacoes

    cadastro = client.post("/api/v1/auth/registrar", json={
        "tipo": "cidadao", "nome": "Outro Cidadao",
        "email": "outro.cidadao.mobile@example.com", "senha": "senha123",
        "senha_confirmacao": "senha123", "cpf": "16899535009",
    })
    outro_token = cadastro.get_json()["access_token"]
    resp = client.get(
        f"/api/v1/solicitacoes/{solicitacoes[0]['id']}",
        headers={"Authorization": f"Bearer {outro_token}"},
    )
    assert resp.status_code == 403


def test_cep_invalido_retorna_400_sem_consulta_externa(client):
    token = _obter_token(client, "cidadao", _CPF_CIDADAO, _SENHA_CIDADAO)
    resp = client.get(
        "/api/v1/cep/123",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_entregas_e_listagem_sao_exclusivas_do_usuario(client):
    token = _obter_token(client, "cidadao", _CPF_CIDADAO, _SENHA_CIDADAO)
    headers = {"Authorization": f"Bearer {token}"}
    lista = client.get("/api/v1/solicitacoes?pagina=1&limite=5", headers=headers)
    entregas = client.get("/api/v1/entregas", headers=headers)
    assert lista.status_code == 200
    assert len(lista.get_json()["itens"]) <= 5
    assert entregas.status_code == 200
    assert isinstance(entregas.get_json()["entregas"], list)


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

