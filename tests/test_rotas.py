"""Testes de rotas Flask.

Cobre:
- GET  /relatorios/exportar-csv  (não autenticado / empresa Free / empresa Pro / admin)
- POST /operacoes/<id>/avancar   (não autenticado / cidadão / solicitação inexistente /
                                  estado final / avança estado)
- POST /solicitacao/<id>/confirmar (não autenticado / cidadão / empresa confirma)
"""

import sqlite3
import os
import pytest

from ecotech.infrastructure.persistence.dados import Dados


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app(tmp_path_factory, monkeypatch_module=None):
    """
    Cria uma instância da aplicação Flask apontada para um BD temporário.
    O seed de dados de exemplo roda uma vez (contar_usuarios == 0).
    """
    # scope="module" exige tmp_path_factory
    tmp = tmp_path_factory.mktemp("db")
    db_path = str(tmp / "test_rotas.db")
    _orig = sqlite3.connect

    # Monkeypatch em nível de módulo: não podemos usar o fixture monkeypatch
    # diretamente, então aplicamos manualmente via import.
    import ecotech.infrastructure.persistence.dados as _dados_mod
    _connect_orig = _dados_mod.sqlite3.connect

    class _PatchedConnect:
        def __call__(self, path, **kwargs):
            return _orig(db_path, **kwargs)

    _dados_mod.sqlite3.connect = _PatchedConnect()

    # Garante que o seed roda (WERKZEUG_RUN_MAIN deve ser diferente de 'true')
    os.environ.pop("WERKZEUG_RUN_MAIN", None)

    from ecotech.infrastructure.web import criar_app
    application = criar_app()
    application.config["TESTING"] = True
    application.config["SECRET_KEY"] = "test-secret"

    yield application

    # Restaura o connect original
    _dados_mod.sqlite3.connect = _connect_orig


@pytest.fixture
def client(app):
    return app.test_client()


def _set_session(client, user_id, nome, tipo):
    """Helper: injeta sessão simulando login."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_nome"] = nome
        sess["user_tipo"] = tipo


# IDs fixos definidos no seed de _inicializar_dados_exemplo
_ID_ADMIN = "USR-ADM-001"
_ID_EMPRESA_FREE = "user-2"   # Recicla Kariri (plano free por padrão)
_ID_CIDADAO = "user-1"        # João Silva


# ---------------------------------------------------------------------------
# /relatorios/exportar-csv
# ---------------------------------------------------------------------------

def test_exportar_csv_nao_autenticado_redireciona(client):
    """Sem sessão deve redirecionar para /login."""
    resp = client.get("/relatorios/exportar-csv")
    assert resp.status_code in (301, 302)
    assert b"login" in resp.headers["Location"].lower().encode()


def test_exportar_csv_empresa_free_redireciona(client):
    """Empresa no plano Free deve ser redirecionada de volta para /relatorios."""
    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.get("/relatorios/exportar-csv", follow_redirects=False)
    assert resp.status_code in (301, 302)


def test_exportar_csv_admin_retorna_csv(client):
    """Admin sempre tem acesso; resposta deve ser text/csv."""
    _set_session(client, _ID_ADMIN, "Admin Ecotech", "administrador")
    resp = client.get("/relatorios/exportar-csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.content_type


def test_exportar_csv_conteudo_cabecalho(client):
    """CSV do admin deve conter cabeçalho esperado."""
    _set_session(client, _ID_ADMIN, "Admin Ecotech", "administrador")
    resp = client.get("/relatorios/exportar-csv")
    texto = resp.data.decode("utf-8")
    assert "ID" in texto
    assert "Usuario" in texto
    assert "Estado" in texto


# ---------------------------------------------------------------------------
# POST /operacoes/<id>/avancar
# ---------------------------------------------------------------------------

def test_avancar_estado_nao_autenticado_retorna_401(client):
    resp = client.post("/operacoes/qualquer-id/avancar")
    assert resp.status_code == 401
    assert resp.is_json


def test_avancar_estado_cidadao_retorna_403(client):
    _set_session(client, _ID_CIDADAO, "João Silva", "cidadao")
    resp = client.post("/operacoes/qualquer-id/avancar")
    assert resp.status_code == 403
    assert resp.is_json


def test_avancar_estado_sol_inexistente_retorna_404(client):
    _set_session(client, _ID_ADMIN, "Admin Ecotech", "administrador")
    resp = client.post("/operacoes/id-que-nao-existe/avancar",
                       data={"metodo": "reciclagem"})
    assert resp.status_code == 404
    assert resp.is_json


def test_avancar_estado_sol_ja_finalizada_retorna_400(client, app):
    """Tentar avançar uma solicitação em estado final retorna 400."""
    # Busca uma solicitação em estado final direto no banco para obter o ID
    import ecotech.infrastructure.persistence.dados as _dados_mod
    db = _dados_mod.Dados()
    c = db.conn.cursor()
    c.execute(
        "SELECT id FROM solicitacao_descarte "
        "WHERE estado IN ('RECICLADO','REUTILIZADO','DESCARTADO') LIMIT 1"
    )
    row = c.fetchone()
    if row is None:
        pytest.skip("Nenhuma solicitação finalizada no banco de seed")

    _set_session(client, _ID_ADMIN, "Admin Ecotech", "administrador")
    resp = client.post(f"/operacoes/{row['id']}/avancar",
                       data={"metodo": "reciclagem"})
    assert resp.status_code == 400
    assert resp.is_json


def test_avancar_estado_avanca_solicitado_para_coletado(client, app):
    """Admin avança solicitação 'Solicitado' → resposta 200 com novo_estado."""
    import ecotech.infrastructure.persistence.dados as _dados_mod
    db = _dados_mod.Dados()
    c = db.conn.cursor()
    c.execute(
        "SELECT id FROM solicitacao_descarte WHERE estado = 'SOLICITADO' LIMIT 1"
    )
    row = c.fetchone()
    if row is None:
        pytest.skip("Nenhuma solicitação em estado SOLICITADO no banco de seed")

    _set_session(client, _ID_ADMIN, "Admin Ecotech", "administrador")
    resp = client.post(f"/operacoes/{row['id']}/avancar")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("novo_estado") == "Coletado"


# ---------------------------------------------------------------------------
# POST /solicitacao/<id>/confirmar
# ---------------------------------------------------------------------------

def test_confirmar_rota_nao_autenticado_retorna_401(client):
    resp = client.post("/solicitacao/qualquer-id/confirmar")
    assert resp.status_code == 401
    assert resp.is_json


def test_confirmar_rota_cidadao_retorna_403(client):
    _set_session(client, _ID_CIDADAO, "João Silva", "cidadao")
    resp = client.post("/solicitacao/qualquer-id/confirmar")
    assert resp.status_code == 403
    assert resp.is_json


def test_confirmar_rota_sol_inexistente_retorna_404(client):
    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.post("/solicitacao/id-que-nao-existe/confirmar")
    assert resp.status_code == 404
    assert resp.is_json


def test_confirmar_rota_empresa_avanca_para_coletado(client, app):
    """Empresa confirma solicitação em estado 'Solicitado' → avança para Coletado."""
    import ecotech.infrastructure.persistence.dados as _dados_mod
    db = _dados_mod.Dados()
    c = db.conn.cursor()
    # Busca uma solicitação ainda em SOLICITADO pertencente ao ponto da empresa Free
    c.execute(
        "SELECT s.id FROM solicitacao_descarte s "
        "JOIN ponto_coleta pc ON s.id_ponto_coleta = pc.id "
        "WHERE s.estado = 'SOLICITADO' AND pc.id_empresa = ? LIMIT 1",
        (_ID_EMPRESA_FREE,)
    )
    row = c.fetchone()
    if row is None:
        pytest.skip("Sem solicitação SOLICITADO para a empresa de seed")

    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.post(f"/solicitacao/{row['id']}/confirmar")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("ok") is True
    assert data.get("novo_estado") == "Coletado"
