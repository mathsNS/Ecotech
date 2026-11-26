"""Testes de regressao do Lote 1A (B-01 a B-11 + regra 0.5b)."""

import os
import sqlite3
from datetime import datetime, timedelta

import pytest

from ecotech.application.services import ServicoDescarte
from ecotech.domain.descarte import ItemDescarte, PontoColeta, SolicitacaoDescarte
from ecotech.domain.dispositivos import Celular
from ecotech.domain.logistica import BaseOperacional
from ecotech.domain.usuarios import Cidadao, Empresa
from ecotech.infrastructure.persistence.dados import Dados


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    """Cria uma app Flask isolada com banco SQLite proprio por teste."""
    db_path = str(tmp_path / "lote1a.db")
    orig_connect = sqlite3.connect

    import ecotech.infrastructure.persistence.dados as dados_mod

    monkeypatch.setattr(
        dados_mod.sqlite3,
        "connect",
        lambda path, **kwargs: orig_connect(db_path, **kwargs),
    )
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)

    from ecotech.infrastructure.web import criar_app

    app = criar_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key-com-pelo-menos-32-bytes"
    return app


def _login_api(client, tipo, credencial, senha):
    resp = client.post(
        "/api/v1/auth/login",
        json={"tipo": tipo, "credencial": credencial, "senha": senha},
    )
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["access_token"]


def _set_web_session(client, user_id, nome, tipo):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_nome"] = nome
        sess["user_tipo"] = tipo


# ---------------------------------------------------------------------------
# B-01: Normalizacao de subcategorias mobile -> tabela_precos
# ---------------------------------------------------------------------------

def test_normalizacao_subcategorias_mobile_para_tabela_precos(isolated_app):
    casos = {
        "Smartphone": "smartphone_medio",
        "Notebook": "notebook_basico",
        "Tablet": "notebook_basico",
        "Geladeira": "geladeira",
        "Televisor": "tv",
        "Ar-condicionado": "ar_condicionado",
        "Micro-ondas": "micro_ondas",
        "Máquina de lavar": "lavadora",
        "smartphone_premium": "smartphone_premium",
    }
    db = Dados()
    for entrada, esperado in casos.items():
        canonica = ServicoDescarte.normalizar_subcategoria(entrada)
        assert canonica == esperado
        assert db.buscar_preco_subcategoria(canonica) is not None

    client = isolated_app.test_client()
    token_cid = _login_api(client, "cidadao", "12345678909", "cidadao123")
    headers = {"Authorization": f"Bearer {token_cid}"}
    ponto_id = client.get("/api/v1/pontos-coleta", headers=headers).get_json()["pontos"][0]["id"]
    amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    criada = client.post(
        "/api/v1/solicitacoes",
        headers=headers,
        data={
            "tipo_dispositivo": "celular",
            "subcategoria": "Smartphone",
            "nome": "Galaxy S23",
            "ano_fabricacao": "2023",
            "quantidade": "1",
            "peso_kg": "0.2",
            "tipo_coleta": "entrega_ponto",
            "ponto_id": ponto_id,
            "data_coleta": amanha,
            "horario_inicio": "10:00",
            "horario_fim": "12:00",
        },
        content_type="multipart/form-data",
    )
    assert criada.status_code == 201, criada.get_json()
    sol_id = criada.get_json()["id"]
    item = db.buscar_itens_solicitacao(sol_id)[0]
    assert item["subcategoria"] == "smartphone_medio"


# ---------------------------------------------------------------------------
# B-02: Usuario desativado perde acesso imediatamente (API + Web + cache)
# ---------------------------------------------------------------------------

def test_usuario_desativado_bloqueado_imediatamente_api_e_web(isolated_app):
    client = isolated_app.test_client()
    reg = client.post(
        "/api/v1/auth/registrar",
        json={
            "tipo": "cidadao",
            "nome": "Usuario Revogado",
            "email": "revogado@ecotech.test",
            "senha": "senha123",
            "senha_confirmacao": "senha123",
            "cpf": "52998224725",
        },
    )
    assert reg.status_code == 200
    uid = reg.get_json()["usuario"]["id"]
    token_cid = reg.get_json()["access_token"]
    headers_cid = {"Authorization": f"Bearer {token_cid}"}
    assert client.get("/api/v1/auth/me", headers=headers_cid).status_code == 200

    # Sessao web ativa do mesmo usuario
    _set_web_session(client, uid, "Usuario Revogado", "cidadao")
    assert client.get("/dashboard").status_code == 200

    # Admin desativa o usuario
    token_admin = _login_api(client, "administrador", "admin@ecotech.com", "admin123")
    des = client.post(
        f"/api/v1/admin/usuarios/{uid}/desativar",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert des.status_code == 200

    # JWT antigo agora deve retornar 401 em qualquer rota protegida
    assert client.get("/api/v1/auth/me", headers=headers_cid).status_code == 401
    assert client.get("/api/v1/dashboard", headers=headers_cid).status_code == 401

    # Sessao web antiga deve ser limpa e redirecionar para /login
    resp_web = client.get("/dashboard", follow_redirects=False)
    assert resp_web.status_code in (301, 302)
    assert "/login" in resp_web.headers["Location"]


# ---------------------------------------------------------------------------
# B-03 e B-04: Finalizacao atomica, beneficiario correto, pontos=0 e override
# ---------------------------------------------------------------------------

def test_admin_finaliza_creditando_empresa_responsavel_e_reconcilia_override(isolated_app):
    client = isolated_app.test_client()
    db = Dados()

    token_cid = _login_api(client, "cidadao", "12345678909", "cidadao123")
    headers_cid = {"Authorization": f"Bearer {token_cid}"}
    ponto = next(
        p for p in client.get("/api/v1/pontos-coleta", headers=headers_cid).get_json()["pontos"]
        if p["id"]
    )
    ponto_row = db.buscar_ponto_coleta(ponto["id"])
    empresa_id = ponto_row["id_empresa"]
    empresa_nome = db.buscar_usuario(empresa_id)["nome"]
    db.atualizar_plano_empresa(empresa_id, "professional")

    saldo_emp_antes = db.buscar_saldo_empresa(empresa_id)
    pontos_cid_antes = int(db.buscar_cidadao("user-1")["pontos"] or 0)

    amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    criada = client.post(
        "/api/v1/solicitacoes",
        headers=headers_cid,
        data={
            "tipo_dispositivo": "celular",
            "subcategoria": "smartphone_medio",
            "nome": "Pixel Teste",
            "ano_fabricacao": "2024",
            "quantidade": "1",
            "peso_kg": "0.25",
            "tipo_coleta": "entrega_ponto",
            "ponto_id": ponto["id"],
            "data_coleta": amanha,
            "horario_inicio": "10:00",
            "horario_fim": "12:00",
        },
        content_type="multipart/form-data",
    )
    assert criada.status_code == 201
    sol_id = criada.get_json()["id"]

    # Admin avanca todo o ciclo com override pendente_doc (valor_proposto=1200 > cap 900 -> aplicado 900)
    token_admin = _login_api(client, "administrador", "admin@ecotech.com", "admin123")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    assert client.post(
        f"/api/v1/operacoes/{sol_id}/avancar",
        headers=headers_admin,
        json={"peso_kg": 0.25},
    ).status_code == 200
    assert client.post(
        f"/api/v1/operacoes/{sol_id}/avancar",
        headers=headers_admin,
        json={},
    ).status_code == 200
    fin = client.post(
        f"/api/v1/operacoes/{sol_id}/avancar",
        headers=headers_admin,
        json={
            "metodo": "reuso",
            "estado_produto": "funcionando",
            "valor_proposto": 1200,
            "justificativa": "Aparelho lacrado com nota fiscal",
        },
    )
    assert fin.status_code == 200, fin.get_json()

    # Beneficiario deve ser a empresa do ponto, NAO 'EcoTech'
    entrega = db.conn.execute(
        "SELECT * FROM entrega WHERE id_solicitacao = ?", (sol_id,)
    ).fetchone()
    assert entrega is not None
    assert entrega["empresa"] == empresa_nome
    assert float(entrega["valor"]) == pytest.approx(90.0)  # 10% de 900 (cap)
    assert db.buscar_saldo_empresa(empresa_id) == pytest.approx(saldo_emp_antes + 765.0)
    assert int(db.buscar_cidadao("user-1")["pontos"]) == pontos_cid_antes + 9000

    # Rejeicao de override via WEB nao deve dar crash (B-03) e deve reconciliar valores (B-04)
    _set_web_session(client, "USR-ADM-001", "Admin Ecotech", "administrador")
    rej = client.post(f"/admin/overrides/{sol_id}/rejeitar", follow_redirects=False)
    assert rej.status_code in (301, 302)

    avaliacao = db.buscar_avaliacao_solicitacao(sol_id)
    assert avaliacao["status_override"] == "rejeitado"
    assert float(avaliacao["valor_proposto"]) == pytest.approx(600.0)

    entrega_pos = db.conn.execute(
        "SELECT * FROM entrega WHERE id_solicitacao = ?", (sol_id,)
    ).fetchone()
    receita_pos = db.conn.execute(
        "SELECT * FROM receita_ecotech WHERE id_solicitacao = ?", (sol_id,)
    ).fetchone()
    assert float(entrega_pos["valor"]) == pytest.approx(60.0)
    assert float(receita_pos["valor"]) == pytest.approx(30.0)
    assert int(db.buscar_cidadao("user-1")["pontos"]) == pontos_cid_antes + 6000
    assert db.buscar_saldo_empresa(empresa_id) == pytest.approx(saldo_emp_antes + 510.0)


def test_finalizacao_com_valor_zero_nao_quebra_por_pontos_nao_positivos(isolated_app):
    client = isolated_app.test_client()
    db = Dados()
    db.conn.execute(
        "UPDATE tabela_precos SET valor_minimo_sucata = 0.0 WHERE subcategoria = 'smartphone_basico'"
    )
    db.conn.commit()

    token_cid = _login_api(client, "cidadao", "12345678909", "cidadao123")
    headers_cid = {"Authorization": f"Bearer {token_cid}"}
    ponto_id = client.get("/api/v1/pontos-coleta", headers=headers_cid).get_json()["pontos"][0]["id"]
    amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    sol_id = client.post(
        "/api/v1/solicitacoes",
        headers=headers_cid,
        data={
            "tipo_dispositivo": "celular",
            "subcategoria": "smartphone_basico",
            "nome": "Sucata Zero",
            "ano_fabricacao": "2018",
            "quantidade": "1",
            "peso_kg": "0.15",
            "tipo_coleta": "entrega_ponto",
            "ponto_id": ponto_id,
            "data_coleta": amanha,
            "horario_inicio": "10:00",
            "horario_fim": "12:00",
        },
        content_type="multipart/form-data",
    ).get_json()["id"]

    token_admin = _login_api(client, "administrador", "admin@ecotech.com", "admin123")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    client.post(f"/api/v1/operacoes/{sol_id}/avancar", headers=headers_admin, json={"peso_kg": 0.15})
    client.post(f"/api/v1/operacoes/{sol_id}/avancar", headers=headers_admin, json={})
    fin = client.post(
        f"/api/v1/operacoes/{sol_id}/avancar",
        headers=headers_admin,
        json={"metodo": "reciclagem", "estado_produto": "sucata"},
    )
    assert fin.status_code == 200, fin.get_json()
    assert fin.get_json()["novo_estado"] == "Reciclado"


# ---------------------------------------------------------------------------
# B-05: Saque atomico e persistencia de titular
# ---------------------------------------------------------------------------

def test_saque_persiste_titular_e_valida_saldo_atomicamente(isolated_app):
    client = isolated_app.test_client()
    db = Dados()
    db.conn.execute("UPDATE cidadao SET pontos = 1500 WHERE id_usuario = 'user-1'")
    db.conn.execute("DELETE FROM saque WHERE id_usuario = 'user-1'")
    db.conn.commit()

    token_cid = _login_api(client, "cidadao", "12345678909", "cidadao123")
    headers = {"Authorization": f"Bearer {token_cid}"}

    resp = client.post(
        "/api/v1/saques",
        headers=headers,
        json={
            "valor": 10.0,
            "metodo": "Pix",
            "titular": "Joao da Silva Titular",
            "id_cliente": "saque-lote1a-1",
        },
    )
    assert resp.status_code == 201, resp.get_json()
    assert resp.get_json()["saque"]["titular"] == "Joao da Silva Titular"

    carteira = client.get("/api/v1/carteira", headers=headers).get_json()
    assert carteira["saques"][0]["titular"] == "Joao da Silva Titular"
    assert carteira["saldo"] == pytest.approx(5.0)

    # Tentativa de saque com saldo insuficiente deve falhar atomicamente mesmo com chave nova
    excedente = client.post(
        "/api/v1/saques",
        headers=headers,
        json={
            "valor": 6.0,
            "metodo": "Pix",
            "titular": "Joao da Silva Titular",
            "id_cliente": "saque-lote1a-2",
        },
    )
    assert excedente.status_code == 400


# ---------------------------------------------------------------------------
# B-06: DESCARTADO libera capacidade e carga da base operacional
# ---------------------------------------------------------------------------

def test_estado_descartado_nao_bloqueia_carga_nem_capacidade_da_base(tmp_path, monkeypatch):
    db_path = str(tmp_path / "base_descartado.db")
    orig = sqlite3.connect
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: orig(db_path, **kwargs),
    )
    db = Dados()
    cid = Cidadao("c-1", "Maria", "maria@test.com", "12345678909")
    emp = Empresa("e-1", "Recicla", "rec@test.com", "11222333000181", "Recicla LTDA")
    db.salvar_cidadao(cid)
    db.salvar_empresa(emp)
    base = BaseOperacional("b-1", "e-1", "Base 1", "Rua 1", -7.2, -39.3, 25.0, 100.0)
    db.salvar_base_operacional(base)

    sol = SolicitacaoDescarte("sol-desc", cid, None)
    disp = Celular("d-1", "Celular", 20.0)
    sol.adicionar_item(ItemDescarte(disp, 1))
    db.salvar_solicitacao(sol)
    db.salvar_dispositivo(disp)
    db.salvar_itens_descarte(sol.id, sol.itens[0])
    db.conn.execute(
        "UPDATE solicitacao_descarte SET base_operacional_id = 'b-1', estado = 'DESCARTADO' WHERE id = 'sol-desc'"
    )
    db.conn.commit()

    candidata = next(r for r in db.buscar_bases_candidatas() if r["id"] == "b-1")
    assert candidata["carga_operacional"] == 0
    assert float(candidata["capacidade_comprometida_kg"]) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# B-07: Datas ISO em ordenacao e julianday() no diagnostico de despacho
# ---------------------------------------------------------------------------

def test_ordenacao_cronologica_notificacoes_e_julianday_despacho(tmp_path, monkeypatch):
    db_path = str(tmp_path / "datas.db")
    orig = sqlite3.connect
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: orig(db_path, **kwargs),
    )
    db = Dados()
    cid = Cidadao("c-1", "Maria", "maria@test.com", "12345678909")
    emp = Empresa("e-1", "Recicla", "rec@test.com", "11222333000181", "Recicla LTDA")
    db.salvar_cidadao(cid)
    db.salvar_empresa(emp)

    # Notificacao de 02/01/2027 deve vir ANTES de 31/12/2026 (nao ordem lexicografica!)
    db.conn.execute(
        "INSERT INTO notificacao (id_usuario, timestamp, mensagem) VALUES ('c-1', '31/12/2026 23:00:00', 'Antiga')"
    )
    db.conn.execute(
        "INSERT INTO notificacao (id_usuario, timestamp, mensagem) VALUES ('c-1', '02/01/2027 08:00:00', 'Nova')"
    )
    db.conn.commit()
    notifs = db.buscar_notificacoes_usuario("c-1")
    assert notifs[0]["mensagem"] == "Nova"
    assert notifs[1]["mensagem"] == "Antiga"

    # Diagnostico de despacho com data_criacao em formato BR DD/MM/YYYY HH:MM
    base = BaseOperacional("b-1", "e-1", "Base 1", "Rua 1", -7.2, -39.3, 25.0, 100.0)
    db.salvar_base_operacional(base)
    db.conn.execute(
        "INSERT INTO solicitacao_descarte (id, id_usuario, estado, data_criacao) "
        "VALUES ('s-1', 'c-1', 'BUSCANDO_EMPRESA', '10/09/2026 10:00')"
    )
    db.conn.execute(
        "INSERT INTO oferta_coleta "
        "(id, solicitacao_id, empresa_id, base_operacional_id, distancia_km, score_prioridade, prioridade, rodada, status, snapshot_fatores, criada_em) "
        "VALUES ('of-1', 's-1', 'e-1', 'b-1', 1.0, 1.0, 1, 1, 'ATIVA', '{}', '2026-09-10T10:15:00')"
    )
    db.conn.commit()
    metricas = db.buscar_diagnostico_despacho()["metricas"]
    assert metricas["minutos_ate_primeira_oferta"] == pytest.approx(15.0, abs=0.1)


# ---------------------------------------------------------------------------
# B-08, B-09, B-10, B-11 e 0.5b
# ---------------------------------------------------------------------------

def test_cache_perfil_notificacoes_busca_admin_relatorios_e_confirmar(isolated_app):
    client = isolated_app.test_client()
    db = Dados()

    # B-08: PATCH /perfil atualiza imediatamente GET /auth/me
    reg = client.post(
        "/api/v1/auth/registrar",
        json={
            "tipo": "cidadao",
            "nome": "Nome Inicial",
            "email": "inicial.lote1a@ecotech.test",
            "senha": "senha123",
            "senha_confirmacao": "senha123",
            "cpf": "39053344705",
        },
    )
    token_novo = reg.get_json()["access_token"]
    headers_novo = {"Authorization": f"Bearer {token_novo}"}
    assert client.patch(
        "/api/v1/perfil",
        headers=headers_novo,
        json={"nome": "Nome Sincronizado", "email": "sincronizado.lote1a@ecotech.test"},
    ).status_code == 200
    me = client.get("/api/v1/auth/me", headers=headers_novo).get_json()
    assert me["nome"] == "Nome Sincronizado"
    assert me["email"] == "sincronizado.lote1a@ecotech.test"

    # B-10: Busca Admin encontra por email completo e CPF completo ANTES do mascaramento
    token_admin = _login_api(client, "administrador", "admin@ecotech.com", "admin123")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    por_email = client.get(
        "/api/v1/admin/usuarios?busca=sincronizado.lote1a@ecotech.test",
        headers=headers_admin,
    ).get_json()
    assert por_email["paginacao"]["total"] == 1
    assert "*" in por_email["usuarios"][0]["email"]

    por_cpf = client.get(
        "/api/v1/admin/usuarios?busca=390.533.447-05",
        headers=headers_admin,
    ).get_json()
    assert por_cpf["paginacao"]["total"] == 1
    assert "*" in por_cpf["usuarios"][0]["documento"]

    # B-09: Notificacao de entrega em ponto tem texto rico e deep link direto para a operacao
    ponto = client.get("/api/v1/pontos-coleta", headers=headers_novo).get_json()["pontos"][0]
    ponto_row = db.buscar_ponto_coleta(ponto["id"])
    amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    sol_resp = client.post(
        "/api/v1/solicitacoes",
        headers=headers_novo,
        data={
            "tipo_dispositivo": "computador",
            "subcategoria": "Notebook",
            "nome": "Dell Inspiron",
            "ano_fabricacao": "2022",
            "quantidade": "1",
            "peso_kg": "2.5",
            "tipo_coleta": "entrega_ponto",
            "ponto_id": ponto["id"],
            "data_coleta": amanha,
            "horario_inicio": "09:00",
            "horario_fim": "11:00",
        },
        content_type="multipart/form-data",
    )
    assert sol_resp.status_code == 201
    sol_id = sol_resp.get_json()["id"]

    # Verifica deep link para a empresa dona do ponto
    emp_row = db.buscar_empresa(ponto_row["id_empresa"])
    token_emp = _login_api(client, "empresa", emp_row["cnpj"], "empresa123")
    notifs_emp = client.get(
        "/api/v1/notificacoes",
        headers={"Authorization": f"Bearer {token_emp}"},
    ).get_json()["notificacoes"]
    notif_ponto = next(n for n in notifs_emp if ponto["nome"] in n["mensagem"])
    assert notif_ponto["destino"] == f"/empresa/operacoes/{sol_id}"
    assert "2.5 kg" in notif_ponto["mensagem"]

    # B-09: Deep link de coleta:<id>:atribuida tambem resolve para detalhes
    db.salvar_notificacao(
        ponto_row["id_empresa"],
        "Coleta aceita.",
        chave_idempotencia=f"coleta:{sol_id}:atribuida:empresa",
    )
    notifs_emp2 = client.get(
        "/api/v1/notificacoes",
        headers={"Authorization": f"Bearer {token_emp}"},
    ).get_json()["notificacoes"]
    notif_aceite = next(n for n in notifs_emp2 if n["mensagem"] == "Coleta aceita.")
    assert notif_aceite["destino"] == f"/empresa/operacoes/{sol_id}"

    # 0.5b: Web /relatorios bloqueia cidadao e navbar oculta link
    _set_web_session(client, "user-1", "João Silva", "cidadao")
    rel_cid = client.get("/relatorios", follow_redirects=False)
    assert rel_cid.status_code in (301, 302)
    assert "/dashboard" in rel_cid.headers["Location"]
    dash_cid_html = client.get("/dashboard").data.decode("utf-8")
    assert 'href="/relatorios"' not in dash_cid_html

    # B-11: Web /nova-solicitacao com horario invalido nao grava solicitacao orfa
    antes_sols = db.contar_solicitacoes()
    resp_inv = client.post(
        "/nova-solicitacao",
        data={
            "tipo_dispositivo": "celular",
            "subcategoria": "smartphone_medio",
            "nome": "Orfao Teste",
            "peso_kg": "0.5",
            "quantidade": "1",
            "tipo_coleta": "domiciliar",
            "endereco_coleta": "Rua Invalida, 1",
            "latitude_coleta": "-7.21",
            "longitude_coleta": "-39.31",
            "data_coleta": amanha,
            "horario_coleta": "16:00",
            "horario_fim": "14:00",
        },
    )
    assert resp_inv.status_code == 200
    assert db.contar_solicitacoes() == antes_sols

    # B-11: Web /solicitacao/<id>/confirmar grava confirmado_empresa=1 e peso_aferido_kg
    _set_web_session(client, ponto_row["id_empresa"], emp_row["nome"], "empresa")
    conf = client.post(
        f"/solicitacao/{sol_id}/confirmar",
        data={"peso_aferido_kg": "2.8"},
    )
    assert conf.status_code == 200
    assert db.buscar_confirmacoes_solicitacao(sol_id)["confirmado_empresa"] == 1
    assert float(db.buscar_solicitacao(sol_id)["peso_confirmado_kg"]) == pytest.approx(2.8)

    # B-08: Mudanca externa direta no SQLite (ex.: CLI processar-ofertas) reflete no cache da API
    db.conn.execute(
        "UPDATE solicitacao_descarte SET estado = 'EM_PROCESSAMENTO' WHERE id = ?",
        (sol_id,),
    )
    db.conn.commit()
    det_sync = client.get(f"/api/v1/solicitacoes/{sol_id}", headers=headers_novo)
    assert det_sync.status_code == 200
    assert det_sync.get_json()["estado"] == "Em Processamento"

    # B-04: Web /operacoes/<id>/avancar exige justificativa para override pendente_doc
    sem_just = client.post(
        f"/operacoes/{sol_id}/avancar",
        data={
            "metodo": "reuso",
            "estado_produto": "funcionando",
            "valor_proposto": "5000",
            "justificativa": "",
        },
    )
    assert sem_just.status_code == 400

    # B-11: Web CSV respeita filtro de periodo e inclui BOM UTF-8
    _set_web_session(client, "USR-ADM-001", "Admin Ecotech", "administrador")
    csv_vazio = client.get(
        "/relatorios/exportar-csv?data_inicio=2099-01-01&data_fim=2099-12-31"
    )
    assert csv_vazio.status_code == 200
    assert csv_vazio.data.startswith("\ufeffID,Usuario".encode("utf-8"))
    linhas = [l for l in csv_vazio.data.decode("utf-8-sig").splitlines() if l.strip()]
    assert len(linhas) == 1

    # B-11: CO2 evitado no dashboard empresa usa a mesma formula dos relatorios
    dash_emp = client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token_emp}"},
    ).get_json()
    rel_emp = client.get(
        "/api/v1/relatorios",
        headers={"Authorization": f"Bearer {token_emp}"},
    ).get_json()
    assert dash_emp["metricas"]["co2_evitado_kg"] == pytest.approx(
        sum(item["impacto_kg"] for item in rel_emp["finalizadas"]), abs=0.1
    )
