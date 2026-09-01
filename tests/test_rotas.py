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
_ID_OUTRA_EMPRESA = "user-7"   # TechLixo Soluções
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


def _buscar_solicitacao_de_outra_empresa(id_empresa):
    import ecotech.infrastructure.persistence.dados as _dados_mod
    db = _dados_mod.Dados()
    return db.conn.execute(
        "SELECT s.id FROM solicitacao_descarte s "
        "JOIN ponto_coleta pc ON s.id_ponto_coleta = pc.id "
        "WHERE pc.id_empresa <> ? LIMIT 1",
        (id_empresa,)
    ).fetchone()


def test_confirmar_rota_outra_empresa_retorna_403(client):
    row = _buscar_solicitacao_de_outra_empresa(_ID_EMPRESA_FREE)
    if row is None:
        pytest.skip("Sem solicitação de outra empresa no seed")

    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.post(f"/solicitacao/{row['id']}/confirmar")

    assert resp.status_code == 403
    assert resp.is_json


def test_avancar_rota_outra_empresa_retorna_403(client):
    row = _buscar_solicitacao_de_outra_empresa(_ID_EMPRESA_FREE)
    if row is None:
        pytest.skip("Sem solicitação de outra empresa no seed")

    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.post(f"/operacoes/{row['id']}/avancar")

    assert resp.status_code == 403
    assert resp.is_json


def test_mtr_outra_empresa_nao_e_gerado(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod
    db = _dados_mod.Dados()
    db.atualizar_plano_empresa(_ID_EMPRESA_FREE, 'professional')
    row = db.conn.execute(
        "SELECT s.id FROM solicitacao_descarte s "
        "JOIN ponto_coleta pc ON s.id_ponto_coleta = pc.id "
        "WHERE pc.id_empresa <> ? LIMIT 1",
        (_ID_EMPRESA_FREE,)
    ).fetchone()
    if row is None:
        pytest.skip("Sem solicitação de outra empresa no seed")

    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.get(f"/solicitacao/{row['id']}/mtr", follow_redirects=False)

    assert resp.status_code in (301, 302)
    assert '/operacoes' in resp.headers['Location']


def test_saque_negado_para_empresa(client):
    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.get('/saque', follow_redirects=False)

    assert resp.status_code in (301, 302)
    assert '/dashboard' in resp.headers['Location']


def test_csrf_rejeita_post_sem_token_quando_habilitado(client, app):
    _set_session(client, _ID_ADMIN, "Admin Ecotech", "administrador")
    app.config['TESTING'] = False
    app.config['CSRF_ENABLED'] = True
    try:
        resp = client.post('/usuarios/user-1/desativar')
    finally:
        app.config['TESTING'] = True

    assert resp.status_code == 400
    assert resp.is_json


def test_csrf_protege_aceite_de_oferta(client, app):
    _set_session(client, _ID_EMPRESA_FREE, 'Recicla Kariri', 'empresa')
    app.config['TESTING'] = False
    app.config['CSRF_ENABLED'] = True
    try:
        resp = client.post('/ofertas/oferta-inexistente/aceitar')
    finally:
        app.config['TESTING'] = True
    assert resp.status_code == 400
    assert resp.is_json


def test_empresa_lista_suas_bases_operacionais(client):
    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.get('/empresa/bases')

    assert resp.status_code == 200
    assert b'Bases operacionais' in resp.data
    assert b'Recicla Kariri' in resp.data


def test_empresa_nao_edita_base_de_outra_empresa(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod
    db = _dados_mod.Dados()
    row = db.conn.execute(
        "SELECT id FROM base_operacional WHERE empresa_id <> ? LIMIT 1",
        (_ID_EMPRESA_FREE,)
    ).fetchone()
    if row is None:
        pytest.skip('Sem base de outra empresa no seed')

    _set_session(client, _ID_EMPRESA_FREE, "Recicla Kariri", "empresa")
    resp = client.post(
        f"/empresa/bases/{row['id']}/editar",
        data={
            'nome': 'Invasão', 'endereco': 'Rua X',
            'latitude': '-7.2', 'longitude': '-39.3',
            'raio_atendimento_km': '10', 'capacidade_kg': '100',
        },
    )
    assert resp.status_code == 403


def _dados_nova_coleta(**sobrescrever):
    dados = {
        'tipo_dispositivo': 'celular',
        'subcategoria': 'smartphone_medio',
        'nome': 'Aparelho Localizado',
        'peso_kg': '1.0',
        'quantidade': '1',
        'tipo_coleta': 'domiciliar',
        'endereco_coleta': 'Rua da Localização, 10',
        'latitude_coleta': '-7.2134',
        'longitude_coleta': '-39.3153',
        'nome_contato': 'João',
        'data_coleta': '2026-09-10',
        'horario_coleta': '14:30',
    }
    dados.update(sobrescrever)
    return dados


def test_coleta_domiciliar_persiste_coordenadas(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod
    _set_session(client, _ID_CIDADAO, "João Silva", "cidadao")
    resp = client.post('/nova-solicitacao', data=_dados_nova_coleta())
    assert resp.status_code in (301, 302)

    db = _dados_mod.Dados()
    row = db.conn.execute("""
        SELECT latitude_coleta, longitude_coleta, origem_localizacao
        FROM solicitacao_descarte
        WHERE endereco_coleta = 'Rua da Localização, 10'
        ORDER BY rowid DESC LIMIT 1
    """).fetchone()
    assert row['latitude_coleta'] == pytest.approx(-7.2134)
    assert row['longitude_coleta'] == pytest.approx(-39.3153)
    assert row['origem_localizacao'] == 'navegador_ou_formulario'
    despacho = db.conn.execute("""
        SELECT estado FROM solicitacao_descarte
        WHERE endereco_coleta = 'Rua da Localização, 10'
        ORDER BY rowid DESC LIMIT 1
    """).fetchone()
    assert despacho['estado'] == 'BUSCANDO_EMPRESA'


def test_coleta_domiciliar_sem_coordenadas_nao_cria_solicitacao(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod
    db = _dados_mod.Dados()
    antes = db.contar_solicitacoes()
    _set_session(client, _ID_CIDADAO, "João Silva", "cidadao")
    resp = client.post(
        '/nova-solicitacao',
        data=_dados_nova_coleta(
            endereco_coleta='Rua Sem Coordenadas',
            latitude_coleta='', longitude_coleta='',
        ),
    )
    assert resp.status_code == 200
    assert _dados_mod.Dados().contar_solicitacoes() == antes


def test_formulario_domiciliar_usa_endereco_sem_coordenadas_visiveis(client):
    _set_session(client, _ID_CIDADAO, "João Silva", "cidadao")
    resp = client.get('/nova-solicitacao?tipo=domiciliar')
    assert resp.status_code == 200
    assert b'CEP' in resp.data
    assert b'latitude_manual' not in resp.data
    assert b'longitude_manual' not in resp.data


def test_comando_processar_ofertas_pode_ser_agendado(app):
    resultado = app.test_cli_runner().invoke(
        args=['processar-ofertas', '--agora', '2026-09-10T14:36:00']
    )
    assert resultado.exit_code == 0
    assert 'oferta(s) ativada(s)' in resultado.output


def test_aceite_exige_login_e_libera_dados_apenas_a_vencedora(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod
    _set_session(client, _ID_CIDADAO, 'João Silva', 'cidadao')
    client.post('/nova-solicitacao', data=_dados_nova_coleta(
        endereco_coleta='Rua Privada do Aceite, 77', nome_contato='Contato Secreto'
    ))
    db = _dados_mod.Dados()
    ofertas = db.conn.execute("""
        SELECT * FROM oferta_coleta
        WHERE solicitacao_id = (
            SELECT id FROM solicitacao_descarte
            WHERE endereco_coleta = 'Rua Privada do Aceite, 77'
            ORDER BY rowid DESC LIMIT 1
        ) ORDER BY prioridade
    """).fetchall()
    ativa = ofertas[0]

    with client.session_transaction() as sess:
        sess.clear()
    assert client.post(f'/ofertas/{ativa["id"]}/aceitar').status_code == 401

    _set_session(client, ativa['empresa_id'], 'Empresa Vencedora', 'empresa')
    resumo = client.get('/api/empresa/ofertas').get_json()['ofertas'][0]
    assert 'endereco_coleta' not in str(resumo)
    resposta = client.post(f'/ofertas/{ativa["id"]}/aceitar')
    assert resposta.status_code == 200
    assert resposta.get_json()['endereco_coleta'] == 'Rua Privada do Aceite, 77'

    operacoes = client.get('/operacoes')
    assert b'Rua Privada do Aceite, 77' in operacoes.data
    agenda_ui = client.get(
        f'/solicitacoes/{ativa["solicitacao_id"]}/agendamento'
    )
    assert agenda_ui.status_code == 200
    assert b'_csrf_token' in agenda_ui.data
    assert b'Abrir chat' in agenda_ui.data
    client.post(
        f'/solicitacoes/{ativa["solicitacao_id"]}/chat',
        data={'texto': '<script>alert(1)</script>'},
    )
    pagina_chat = client.get(f'/solicitacoes/{ativa["solicitacao_id"]}/chat')
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in pagina_chat.data
    assert b'<script>alert(1)</script>' not in pagina_chat.data

    perdedora = next(o for o in ofertas if o['empresa_id'] != ativa['empresa_id'])
    _set_session(client, perdedora['empresa_id'], 'Empresa Perdedora', 'empresa')
    conflito = client.post(f'/ofertas/{perdedora["id"]}/aceitar')
    assert conflito.status_code == 409
    assert b'Rua Privada do Aceite, 77' not in client.get('/operacoes').data
    assert client.get(
        f'/solicitacoes/{ativa["solicitacao_id"]}/chat'
    ).status_code == 403


def test_interfaces_respeitam_papel_privacidade_e_csrf(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod
    _set_session(client, _ID_CIDADAO, 'João Silva', 'cidadao')
    client.post('/nova-solicitacao', data=_dados_nova_coleta(
        endereco_coleta='Rua Invisível Antes do Aceite, 9',
        horario_fim='16:30',
    ))
    db=_dados_mod.Dados()
    oferta=db.conn.execute("""SELECT * FROM oferta_coleta WHERE status='ATIVA'
        AND solicitacao_id=(SELECT id FROM solicitacao_descarte
        WHERE endereco_coleta='Rua Invisível Antes do Aceite, 9' ORDER BY rowid DESC LIMIT 1)
        ORDER BY prioridade LIMIT 1""").fetchone()
    assert client.get('/empresa/oportunidades').status_code in (301,302)
    _set_session(client,oferta['empresa_id'],'Empresa','empresa')
    pagina=client.get('/empresa/oportunidades?pagina=1')
    assert pagina.status_code==200
    assert b'_csrf_token' in pagina.data
    assert b'score' not in pagina.data.lower()
    assert 'Rua Invisível Antes do Aceite'.encode() not in pagina.data
    _set_session(client,_ID_ADMIN,'Admin','administrador')
    admin=client.get('/admin/despacho')
    assert admin.status_code==200 and b'Painel somente leitura' in admin.data
