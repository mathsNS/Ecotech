"""Testes da API JSON /api/v1 usada pelo app mobile.

Cobre:
- POST /api/v1/auth/login (sucesso cidadao/empresa/admin, credencial invalida)
- GET  /api/v1/auth/me    (com token valido, sem token, token invalido)
"""

import io
import json
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
    if tipo == "cidadao":
        assert corpo["total_entregas_concluidas"] >= 0
        assert len(corpo["entregas_recentes"]) <= 6
    if tipo == "empresa":
        assert all(
            "base_operacional" in solicitacao
            for solicitacao in corpo["em_processamento"]
        )


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
    assert set(lista.get_json()["estatisticas"]) == {
        "pendentes", "em_coleta", "processando", "finalizadas"
    }
    assert entregas.status_code == 200
    assert isinstance(entregas.get_json()["entregas"], list)


# ---------------------------------------------------------------------------
# Estrutura e oportunidades da empresa
# ---------------------------------------------------------------------------

def _cabecalho_empresa(client, cnpj=_CNPJ_EMPRESA, senha=_SENHA_EMPRESA):
    token = _obter_token(client, "empresa", cnpj, senha)
    return {"Authorization": f"Bearer {token}"}


def _endereco_empresa(**extras):
    payload = {
        "nome": "Unidade Mobile",
        "cep": "63010010",
        "logradouro": "Rua Sao Pedro",
        "numero": "100",
        "complemento": "Galpao B",
        "bairro": "Centro",
        "cidade": "Juazeiro do Norte",
        "uf": "CE",
        "capacidade_kg": 800,
    }
    payload.update(extras)
    return payload


@pytest.fixture
def cep_empresa(monkeypatch):
    from ecotech.application.geolocalizacao import GeolocalizadorPorCep

    monkeypatch.setattr(GeolocalizadorPorCep, "consultar_cep", lambda self, cep: {
        "street": "Rua Sao Pedro", "neighborhood": "Centro",
        "city": "Juazeiro do Norte", "state": "CE",
        "latitude": -7.213, "longitude": -39.315,
    })


def test_empresa_cria_edita_e_desativa_base_sem_coordenadas_na_api(
    client, cep_empresa,
):
    headers = _cabecalho_empresa(client)
    payload = _endereco_empresa(
        raio_atendimento_km=30,
        realiza_coleta_domiciliar=True,
    )
    criada = client.post('/api/v1/empresa/bases', headers=headers, json=payload)
    assert criada.status_code == 201, criada.get_json()
    base = criada.get_json()
    assert base['endereco'].startswith('Rua Sao Pedro, 100')
    assert 'latitude' not in base and 'longitude' not in base

    payload['nome'] = 'Unidade Mobile Atualizada'
    payload['raio_atendimento_km'] = 35
    editada = client.patch(
        f"/api/v1/empresa/bases/{base['id']}", headers=headers, json=payload
    )
    assert editada.status_code == 200
    assert editada.get_json()['raio_atendimento_km'] == 35

    desativada = client.post(
        f"/api/v1/empresa/bases/{base['id']}/atividade",
        headers=headers, json={'ativa': False},
    )
    assert desativada.status_code == 200
    assert desativada.get_json()['ativa'] is False

    outra = _cabecalho_empresa(client, '14380200000121', 'techlixo123')
    invasao = client.patch(
        f"/api/v1/empresa/bases/{base['id']}", headers=outra, json=payload
    )
    assert invasao.status_code == 403


def test_empresa_gerencia_ponto_e_confirma_entrega_com_peso_aferido(
    client, cep_empresa,
):
    headers_empresa = _cabecalho_empresa(client)
    criada = client.post(
        '/api/v1/empresa/pontos', headers=headers_empresa,
        json=_endereco_empresa(nome='Ponto Mobile', capacidade_kg=500),
    )
    assert criada.status_code == 201, criada.get_json()
    ponto = criada.get_json()
    assert ponto['ativa'] is True

    headers_cidadao = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'cidadao', _CPF_CIDADAO, _SENHA_CIDADAO
        )
    }
    solicitacao = client.post(
        '/api/v1/solicitacoes', headers=headers_cidadao,
        data=_dados_nova_solicitacao(ponto['id']),
        content_type='multipart/form-data',
    )
    assert solicitacao.status_code == 201, solicitacao.get_json()
    solicitacao_id = solicitacao.get_json()['id']

    pontos = client.get('/api/v1/empresa/pontos', headers=headers_empresa)
    ponto_atual = next(
        item for item in pontos.get_json()['pontos'] if item['id'] == ponto['id']
    )
    entrega = next(
        item for item in ponto_atual['solicitacoes']
        if item['id'] == solicitacao_id
    )
    assert entrega['pode_confirmar'] is True
    assert entrega['peso_confirmado_kg'] is None

    confirmada = client.post(
        f"/api/v1/empresa/pontos/{ponto['id']}/solicitacoes/"
        f"{solicitacao_id}/confirmar",
        headers=headers_empresa, json={'peso_kg': '0,55'},
    )
    assert confirmada.status_code == 200, confirmada.get_json()
    assert confirmada.get_json()['peso_confirmado_kg'] == 0.55

    desativado = client.delete(
        f"/api/v1/empresa/pontos/{ponto['id']}", headers=headers_empresa
    )
    assert desativado.status_code == 200
    assert desativado.get_json()['ativa'] is False
    publicos = client.get('/api/v1/pontos-coleta', headers=headers_cidadao)
    assert ponto['id'] not in {item['id'] for item in publicos.get_json()['pontos']}


def test_endpoints_empresariais_bloqueiam_outros_perfis(client):
    token = _obter_token(client, 'cidadao', _CPF_CIDADAO, _SENHA_CIDADAO)
    headers = {'Authorization': f'Bearer {token}'}
    assert client.get('/api/v1/empresa/bases', headers=headers).status_code == 403
    assert client.get('/api/v1/empresa/pontos', headers=headers).status_code == 403
    assert client.get(
        '/api/v1/empresa/oportunidades', headers=headers
    ).status_code == 403


def test_oportunidade_preserva_privacidade_e_aceite_e_atomico(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod

    db = _dados_mod.Dados()
    base_recicla = db.conn.execute(
        "SELECT id FROM base_operacional WHERE empresa_id='user-2' LIMIT 1"
    ).fetchone()['id']
    base_tech = db.conn.execute(
        "SELECT id FROM base_operacional WHERE empresa_id='user-7' LIMIT 1"
    ).fetchone()['id']
    agora = datetime.now()
    solicitacao_id = 'sol-api-oportunidade'
    snapshot = json.dumps({'dados_visiveis': {
        'categorias': ['celular'], 'peso_estimado_kg': 1.2,
        'agendada_para': (agora + timedelta(days=1)).isoformat(timespec='seconds'),
    }})
    with db.conn:
        db.conn.execute("""
            INSERT INTO solicitacao_descarte(
                id,id_usuario,estado,data_criacao,tipo_coleta,endereco_coleta,
                nome_contato,data_agendamento,latitude_coleta,longitude_coleta
            ) VALUES(?,?,'BUSCANDO_EMPRESA',?,'domiciliar',?,?,?,?,?)
        """, (
            solicitacao_id, 'user-1', agora.isoformat(timespec='seconds'),
            'Rua Protegida, 99', 'Contato Privado',
            (agora + timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
            -7.21, -39.31,
        ))
        for oferta_id, empresa_id, base_id, prioridade in (
            ('oferta-api-recicla', 'user-2', base_recicla, 1),
            ('oferta-api-tech', 'user-7', base_tech, 2),
        ):
            db.conn.execute("""
                INSERT INTO oferta_coleta(
                    id,solicitacao_id,empresa_id,base_operacional_id,
                    distancia_km,score_prioridade,prioridade,rodada,status,
                    snapshot_fatores,criada_em,enviada_em,ativada_em,expira_em
                ) VALUES(?,?,?,?,?,100,?,1,'ATIVA',?,?,?,?,?)
            """, (
                oferta_id, solicitacao_id, empresa_id, base_id, 2.5,
                prioridade, snapshot, agora.isoformat(timespec='seconds'),
                agora.isoformat(timespec='seconds'),
                agora.isoformat(timespec='seconds'),
                (agora + timedelta(minutes=10)).isoformat(timespec='seconds'),
            ))

    recicla = _cabecalho_empresa(client)
    lista = client.get('/api/v1/empresa/oportunidades', headers=recicla)
    assert lista.status_code == 200
    oferta = next(
        item for item in lista.get_json()['oportunidades']
        if item['id'] == 'oferta-api-recicla'
    )
    assert oferta['dados']['categorias'] == ['celular']
    assert 'Rua Protegida' not in str(oferta)
    assert 'Contato Privado' not in str(oferta)

    aceita = client.post(
        '/api/v1/empresa/oportunidades/oferta-api-recicla/aceitar',
        headers=recicla,
    )
    assert aceita.status_code == 200
    assert aceita.get_json()['endereco_coleta'] == 'Rua Protegida, 99'

    tech = _cabecalho_empresa(client, '14380200000121', 'techlixo123')
    conflito = client.post(
        '/api/v1/empresa/oportunidades/oferta-api-tech/aceitar', headers=tech
    )
    assert conflito.status_code == 409

    with db.conn:
        db.conn.execute("""
            INSERT INTO solicitacao_descarte(
                id,id_usuario,estado,data_criacao,tipo_coleta,endereco_coleta,
                nome_contato,data_agendamento,latitude_coleta,longitude_coleta
            ) VALUES('sol-api-recusa','user-1','BUSCANDO_EMPRESA',?,
                'domiciliar','Rua Recusada, 10','Contato',?,-7.21,-39.31)
        """, (
            agora.isoformat(timespec='seconds'),
            (agora + timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
        ))
        db.conn.execute("""
            INSERT INTO oferta_coleta(
                id,solicitacao_id,empresa_id,base_operacional_id,
                distancia_km,score_prioridade,prioridade,rodada,status,
                snapshot_fatores,criada_em,enviada_em,ativada_em,expira_em
            ) VALUES('oferta-api-recusa','sol-api-recusa','user-2',?,
                2.5,100,1,1,'ATIVA',?,?,?,?,?)
        """, (
            base_recicla, snapshot, agora.isoformat(timespec='seconds'),
            agora.isoformat(timespec='seconds'),
            agora.isoformat(timespec='seconds'),
            (agora + timedelta(minutes=10)).isoformat(timespec='seconds'),
        ))
    recusada = client.post(
        '/api/v1/empresa/oportunidades/oferta-api-recusa/recusar',
        headers=recicla, json={'motivo': 'Sem veiculo disponivel'},
    )
    assert recusada.status_code == 200
    assert db.conn.execute(
        "SELECT status FROM oferta_coleta WHERE id='oferta-api-recusa'"
    ).fetchone()['status'] == 'RECUSADA'


# ---------------------------------------------------------------------------
# Operacoes, afericao, avaliacao e MTR
# ---------------------------------------------------------------------------

def test_operacao_exige_peso_avalia_produto_e_gera_mtr(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod

    db = _dados_mod.Dados()
    ponto = db.conn.execute("""
        SELECT id FROM ponto_coleta
        WHERE id_empresa = 'user-2' AND ativo = 1 LIMIT 1
    """).fetchone()
    assert ponto is not None
    cidadao = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'cidadao', _CPF_CIDADAO, _SENHA_CIDADAO
        )
    }
    criada = client.post(
        '/api/v1/solicitacoes', headers=cidadao,
        data=_dados_nova_solicitacao(ponto['id']),
        content_type='multipart/form-data',
    )
    assert criada.status_code == 201, criada.get_json()
    solicitacao_id = criada.get_json()['id']
    empresa = _cabecalho_empresa(client)

    lista = client.get(
        '/api/v1/operacoes?estado=Solicitado&busca=' + solicitacao_id[:8],
        headers=empresa,
    )
    assert lista.status_code == 200, lista.get_json()
    assert lista.get_json()['paginacao']['total'] == 1
    assert lista.get_json()['operacoes'][0]['peso_origem'] == 'estimado'

    sem_peso = client.post(
        f'/api/v1/operacoes/{solicitacao_id}/avancar',
        headers=empresa, json={},
    )
    assert sem_peso.status_code == 400
    aferido = client.post(
        f'/api/v1/operacoes/{solicitacao_id}/peso',
        headers=empresa, json={'peso_kg': '2,75'},
    )
    assert aferido.status_code == 200, aferido.get_json()
    assert aferido.get_json()['peso_confirmado_kg'] == 2.75

    for estado_esperado in ('Coletado', 'Em Processamento'):
        resposta = client.post(
            f'/api/v1/operacoes/{solicitacao_id}/avancar',
            headers=empresa, json={},
        )
        assert resposta.status_code == 200, resposta.get_json()
        assert resposta.get_json()['novo_estado'] == estado_esperado

    incompleta = client.post(
        f'/api/v1/operacoes/{solicitacao_id}/avancar',
        headers=empresa, json={},
    )
    assert incompleta.status_code == 400
    finalizada = client.post(
        f'/api/v1/operacoes/{solicitacao_id}/avancar',
        headers=empresa,
        json={'metodo': 'reciclagem', 'estado_produto': 'defeito_leve'},
    )
    assert finalizada.status_code == 200, finalizada.get_json()
    assert finalizada.get_json()['novo_estado'] == 'Reciclado'
    detalhes = finalizada.get_json()['operacao']
    assert detalhes['peso_confirmado_kg'] == 2.75
    assert detalhes['peso_confirmado_por'] == 'Recicla Kariri'
    assert detalhes['avaliacao']['estado_produto'] == 'defeito_leve'
    assert detalhes['itens'][0]['precos']['funcionando'] >= 0

    admin = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'administrador', _EMAIL_ADMIN, _SENHA_ADMIN
        )
    }
    mtr = client.get(
        f'/api/v1/operacoes/{solicitacao_id}/mtr', headers=admin
    )
    assert mtr.status_code == 200
    assert mtr.mimetype == 'application/pdf'
    assert mtr.data.startswith(b'%PDF')


def test_operacoes_bloqueiam_cidadao_e_isolam_empresas(client):
    cidadao = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'cidadao', _CPF_CIDADAO, _SENHA_CIDADAO
        )
    }
    assert client.get('/api/v1/operacoes', headers=cidadao).status_code == 403
    recicla = _cabecalho_empresa(client)
    operacoes = client.get('/api/v1/operacoes', headers=recicla).get_json()
    assert 'estatisticas' in operacoes
    assert operacoes['paginacao']['por_pagina'] == 20
    operacao_recicla = next(
        item for item in operacoes['operacoes']
        if item['empresa'] == 'Recicla Kariri'
    )
    tech = _cabecalho_empresa(client, '14380200000121', 'techlixo123')
    negado = client.get(
        f"/api/v1/operacoes/{operacao_recicla['id']}", headers=tech
    )
    assert negado.status_code == 403


# ---------------------------------------------------------------------------
# Agenda, conversas, notificacoes e badges
# ---------------------------------------------------------------------------

def test_agenda_chat_notificacoes_e_badges_mobile(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod

    db = _dados_mod.Dados()
    ponto = db.conn.execute("""SELECT id FROM ponto_coleta
        WHERE id_empresa='user-2' AND ativo=1 LIMIT 1""").fetchone()
    cidadao = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'cidadao', _CPF_CIDADAO, _SENHA_CIDADAO
        )
    }
    empresa = _cabecalho_empresa(client)
    criada = client.post(
        '/api/v1/solicitacoes', headers=cidadao,
        data=_dados_nova_solicitacao(ponto['id']),
        content_type='multipart/form-data',
    )
    assert criada.status_code == 201, criada.get_json()
    solicitacao_id = criada.get_json()['id']

    agenda = client.get(
        f'/api/v1/solicitacoes/{solicitacao_id}/agendamento', headers=empresa
    )
    assert agenda.status_code == 200, agenda.get_json()
    assert agenda.get_json()['acoes']['pode_aceitar'] is True, agenda.get_json()
    inicio = datetime.now() + timedelta(days=3)
    proposta = client.post(
        f'/api/v1/solicitacoes/{solicitacao_id}/agendamento/propor',
        headers=empresa,
        json={
            'inicio': inicio.isoformat(timespec='seconds'),
            'fim': (inicio + timedelta(hours=2)).isoformat(timespec='seconds'),
        },
    )
    assert proposta.status_code == 200, proposta.get_json()
    assert proposta.get_json()['proposta_autor']['nome'] == 'Recicla Kariri'
    assert proposta.get_json()['acoes']['pode_aceitar'] is False
    auto_aceite = client.post(
        f'/api/v1/solicitacoes/{solicitacao_id}/agendamento/aceitar',
        headers=empresa,
    )
    assert auto_aceite.status_code == 403
    aceite = client.post(
        f'/api/v1/solicitacoes/{solicitacao_id}/agendamento/aceitar',
        headers=cidadao,
    )
    assert aceite.status_code == 200, aceite.get_json()
    assert aceite.get_json()['agenda']['status'] == 'AGENDADO'
    assert aceite.get_json()['historico'][-1]['autor_nome'] == 'João Silva'

    conversa_empresa = client.get('/api/v1/conversas', headers=empresa)
    assert conversa_empresa.status_code == 200
    conversa = next(
        item for item in conversa_empresa.get_json()['conversas']
        if item['solicitacao_id'] == solicitacao_id
    )
    assert conversa['contato_nome'] == 'João Silva'
    assert conversa['ultima_mensagem'] == 'Horario da coleta confirmado'

    texto = '<script>alert(1)</script>'
    primeira = client.post(
        f'/api/v1/conversas/{solicitacao_id}/mensagens',
        headers=cidadao, json={'texto': texto, 'id_cliente': 'msg-mobile-1'},
    )
    repetida = client.post(
        f'/api/v1/conversas/{solicitacao_id}/mensagens',
        headers=cidadao, json={'texto': texto, 'id_cliente': 'msg-mobile-1'},
    )
    assert primeira.status_code == 201, primeira.get_json()
    assert repetida.get_json()['id'] == primeira.get_json()['id']
    mensagens = client.get(
        f'/api/v1/conversas/{solicitacao_id}/mensagens', headers=empresa
    ).get_json()['mensagens']
    mensagem = next(
        item for item in mensagens if item['id'] == primeira.get_json()['id']
    )
    assert mensagem['texto'] == texto
    assert mensagem['remetente']['nome'] == 'João Silva'
    assert mensagem['remetente']['tipo'] == 'cidadao'
    assert mensagem['propria'] is False

    tech = _cabecalho_empresa(client, '14380200000121', 'techlixo123')
    terceiro = client.get(
        f'/api/v1/conversas/{solicitacao_id}/mensagens', headers=tech
    )
    assert terceiro.status_code == 403
    badges = client.get('/api/v1/badges', headers=empresa).get_json()
    assert badges['mensagens'] >= 1
    leitura = client.post(
        f'/api/v1/conversas/{solicitacao_id}/leitura', headers=empresa
    )
    assert leitura.status_code == 200

    notificacoes = client.get('/api/v1/notificacoes', headers=empresa)
    assert notificacoes.status_code == 200
    aviso_chat = next(
        item for item in notificacoes.get_json()['notificacoes']
        if item['tipo'] == 'mensagem' and solicitacao_id in item['destino']
    )
    assert aviso_chat['lida'] is False
    marcada = client.post(
        '/api/v1/notificacoes/leitura', headers=empresa,
        json={'id': aviso_chat['id']},
    )
    assert marcada.status_code == 200


# ---------------------------------------------------------------------------
# Carteira, saques e relatorios
# ---------------------------------------------------------------------------

def test_carteira_e_saque_idempotente_mobile(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod

    db = _dados_mod.Dados()
    db.conn.execute("UPDATE cidadao SET pontos = 5000 WHERE id_usuario = 'user-1'")
    db.conn.commit()
    cidadao = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'cidadao', _CPF_CIDADAO, _SENHA_CIDADAO
        )
    }
    carteira = client.get('/api/v1/carteira', headers=cidadao)
    assert carteira.status_code == 200
    saldo_inicial = carteira.get_json()['saldo']
    assert saldo_inicial >= 10
    assert carteira.get_json()['conversao']['pontos_por_real'] == 100

    payload = {
        'valor': 10,
        'metodo': 'Pix',
        'titular': 'Joao Silva',
        'id_cliente': 'saque-mobile-fase-8',
    }
    primeiro = client.post('/api/v1/saques', headers=cidadao, json=payload)
    repetido = client.post('/api/v1/saques', headers=cidadao, json=payload)
    assert primeiro.status_code == 201, primeiro.get_json()
    assert repetido.status_code == 200, repetido.get_json()
    assert repetido.get_json()['repetido'] is True
    assert repetido.get_json()['saque']['id'] == primeiro.get_json()['saque']['id']
    assert primeiro.get_json()['carteira']['saldo'] == pytest.approx(
        saldo_inicial - 10
    )
    assert 'T' in primeiro.get_json()['saque']['data_hora']

    conflito = client.post(
        '/api/v1/saques', headers=cidadao,
        json={**payload, 'valor': 11},
    )
    assert conflito.status_code == 400
    assert 'outros dados' in conflito.get_json()['erro']


def test_carteira_e_saque_bloqueiam_empresa(client):
    empresa = _cabecalho_empresa(client)
    assert client.get('/api/v1/carteira', headers=empresa).status_code == 403
    assert client.post(
        '/api/v1/saques', headers=empresa,
        json={'valor': 1, 'metodo': 'Pix', 'titular': 'Empresa'},
    ).status_code == 403


def test_relatorios_respeitam_escopo_periodo_plano_e_csv(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod

    recicla = _cabecalho_empresa(client)
    db = _dados_mod.Dados()
    db.atualizar_plano_empresa('user-2', 'free')
    relatorio = client.get('/api/v1/relatorios', headers=recicla)
    assert relatorio.status_code == 200, relatorio.get_json()
    corpo = relatorio.get_json()
    assert corpo['plano'] == 'free'
    assert corpo['pode_exportar'] is False
    assert corpo['metricas']['peso_descartado_kg'] >= 0
    assert all(item['estado'] in ('Reciclado', 'Reutilizado', 'Descartado')
               for item in corpo['finalizadas'])
    assert client.get(
        '/api/v1/relatorios/exportar.csv', headers=recicla
    ).status_code == 403

    db.atualizar_plano_empresa('user-2', 'professional')
    csv_response = client.get(
        '/api/v1/relatorios/exportar.csv', headers=recicla
    )
    assert csv_response.status_code == 200
    assert csv_response.data.startswith('\ufeffID,Cidadao'.encode('utf-8'))
    assert 'attachment' in csv_response.headers['Content-Disposition']

    vazio = client.get(
        '/api/v1/relatorios?data_inicio=2099-01-01&data_fim=2099-12-31',
        headers=recicla,
    )
    assert vazio.status_code == 200
    assert vazio.get_json()['metricas']['peso_total_kg'] == 0
    invalido = client.get(
        '/api/v1/relatorios?data_inicio=2026-12-31&data_fim=2026-01-01',
        headers=recicla,
    )
    assert invalido.status_code == 400

    cidadao = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'cidadao', _CPF_CIDADAO, _SENHA_CIDADAO
        )
    }
    assert client.get('/api/v1/relatorios', headers=cidadao).status_code == 403
    admin = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'administrador', _EMAIL_ADMIN, _SENHA_ADMIN
        )
    }
    geral = client.get('/api/v1/relatorios', headers=admin)
    assert geral.status_code == 200
    assert geral.get_json()['pode_exportar'] is True


# ---------------------------------------------------------------------------
# Administracao mobile
# ---------------------------------------------------------------------------

def _cabecalho_admin(client):
    return {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'administrador', _EMAIL_ADMIN, _SENHA_ADMIN
        )
    }


def test_admin_usuarios_cadastro_busca_paginacao_e_soft_delete(client):
    admin = _cabecalho_admin(client)
    lista = client.get(
        '/api/v1/admin/usuarios?tipo=cidadao&pagina=1&por_pagina=2',
        headers=admin,
    )
    assert lista.status_code == 200, lista.get_json()
    assert lista.get_json()['paginacao']['por_pagina'] == 2
    assert lista.get_json()['metricas']['cidadaos'] >= 1
    assert all('*' in item['documento'] for item in lista.get_json()['usuarios'])
    assert all('*' in item['email'] for item in lista.get_json()['usuarios'])

    criado = client.post(
        '/api/v1/admin/usuarios', headers=admin,
        json={
            'tipo': 'cidadao',
            'nome': 'Usuario Administrado',
            'email': 'administrado@ecotech.test',
            'senha': 'senha123',
            'cpf': '93541134780',
        },
    )
    assert criado.status_code == 201, criado.get_json()
    usuario_id = criado.get_json()['id']
    filtrado = client.get(
        '/api/v1/admin/usuarios?busca=administrado', headers=admin
    ).get_json()
    assert filtrado['paginacao']['total'] == 1
    assert filtrado['usuarios'][0]['ativo'] is True

    desativado = client.post(
        f'/api/v1/admin/usuarios/{usuario_id}/desativar', headers=admin
    )
    repetido = client.post(
        f'/api/v1/admin/usuarios/{usuario_id}/desativar', headers=admin
    )
    assert desativado.status_code == 200
    assert repetido.get_json()['repetido'] is True
    preservado = client.get(
        '/api/v1/admin/usuarios?busca=administrado', headers=admin
    ).get_json()['usuarios'][0]
    assert preservado['ativo'] is False


def test_admin_despacho_expoe_destinatarios_reais(client):
    admin = _cabecalho_admin(client)
    resposta = client.get('/api/v1/admin/despacho', headers=admin)
    assert resposta.status_code == 200, resposta.get_json()
    corpo = resposta.get_json()
    assert corpo['somente_leitura'] is True
    assert 'solicitacoes_ofertadas' in corpo['metricas']
    assert all(item['empresa_nome'] and item['base_nome']
               for item in corpo['destinatarios'])
    assert all(item['empresa_nome'] for item in corpo['atribuicoes'])


def test_admin_override_decisao_idempotente_e_notifica_empresa(client):
    import ecotech.infrastructure.persistence.dados as _dados_mod

    db = _dados_mod.Dados()
    solicitacao = db.conn.execute("""
        SELECT DISTINCT sd.id,
               COALESCE(sd.empresa_responsavel_id, pc.id_empresa) empresa_id
        FROM solicitacao_descarte sd
        JOIN item_descarte i ON i.id_solicitacao=sd.id
        JOIN dispositivo d ON d.id=i.id_dispositivo
        JOIN tabela_precos tp ON tp.subcategoria=d.subcategoria
        LEFT JOIN ponto_coleta pc ON pc.id=sd.id_ponto_coleta
        WHERE COALESCE(sd.empresa_responsavel_id, pc.id_empresa) IS NOT NULL
        LIMIT 1
    """).fetchone()
    assert solicitacao is not None
    db.conn.execute("""
        UPDATE solicitacao_descarte
        SET estado_produto='funcionando', valor_proposto=99999,
            justificativa_valor='Laudo tecnico anexado',
            status_override='pendente_doc'
        WHERE id=?
    """, (solicitacao['id'],))
    db.conn.commit()
    admin = _cabecalho_admin(client)
    fila = client.get('/api/v1/admin/overrides', headers=admin)
    assert fila.status_code == 200
    item = next(
        item for item in fila.get_json()['overrides']
        if item['solicitacao_id'] == solicitacao['id']
    )
    assert item['valor_base'] > 0
    assert item['limite_override'] == pytest.approx(item['valor_base'] * 1.5)
    assert item['empresa'] != 'Nao atribuida'

    url = f"/api/v1/admin/overrides/{solicitacao['id']}/decisao"
    primeira = client.post(url, headers=admin, json={'decisao': 'rejeitar'})
    repetida = client.post(url, headers=admin, json={'decisao': 'rejeitar'})
    assert primeira.status_code == 200, primeira.get_json()
    assert primeira.get_json()['status'] == 'rejeitado'
    assert repetida.get_json()['repetido'] is True
    notificacao = db.conn.execute("""
        SELECT * FROM notificacao WHERE id_usuario=?
        AND chave_idempotencia=?
    """, (
        solicitacao['empresa_id'],
        f"override:{solicitacao['id']}:rejeitado",
    )).fetchone()
    assert notificacao is not None


def test_admin_precos_valida_edicao_e_bloqueia_nao_admin(client):
    admin = _cabecalho_admin(client)
    tabela = client.get('/api/v1/admin/precos', headers=admin)
    assert tabela.status_code == 200
    atual = next(
        item for item in tabela.get_json()['precos']
        if item['subcategoria'] == 'smartphone_basico'
    )
    invalido = client.patch(
        '/api/v1/admin/precos', headers=admin,
        json={
            'subcategoria': atual['subcategoria'],
            'valor_base': 10,
            'valor_minimo': 10,
        },
    )
    assert invalido.status_code == 400
    alterado = client.patch(
        '/api/v1/admin/precos', headers=admin,
        json={
            'subcategoria': atual['subcategoria'],
            'valor_base': atual['valor_base'] + 1,
            'valor_minimo': atual['valor_minimo'],
        },
    )
    assert alterado.status_code == 200
    atualizado = next(
        item for item in alterado.get_json()['precos']
        if item['subcategoria'] == atual['subcategoria']
    )
    assert atualizado['valor_base'] == atual['valor_base'] + 1

    restaurado = client.patch(
        '/api/v1/admin/precos', headers=admin,
        json={
            'subcategoria': atual['subcategoria'],
            'valor_base': atual['valor_base'],
            'valor_minimo': atual['valor_minimo'],
        },
    )
    assert restaurado.status_code == 200
    empresa = _cabecalho_empresa(client)
    for rota in (
        '/api/v1/admin/usuarios',
        '/api/v1/admin/despacho',
        '/api/v1/admin/overrides',
        '/api/v1/admin/precos',
    ):
        assert client.get(rota, headers=empresa).status_code == 403


def test_planos_expoe_catalogo_limites_e_feature_flags(client):
    empresa = _cabecalho_empresa(client)
    resposta = client.get('/api/v1/planos', headers=empresa)
    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo['plano_atual'] in {'free', 'professional', 'enterprise'}
    assert [item['id'] for item in corpo['planos']] == [
        'free', 'professional', 'enterprise'
    ]
    free, professional, enterprise = corpo['planos']
    assert free['limite_solicitacoes_mes'] == 30
    assert professional['limite_solicitacoes_mes'] is None
    assert professional['feature_flags']['mtr'] is True
    assert enterprise['feature_flags']['api_integracao'] is True
    assert corpo['feature_flags'] == next(
        item['feature_flags'] for item in corpo['planos']
        if item['id'] == corpo['plano_atual']
    )


def test_alteracao_de_plano_valida_perfil_e_e_idempotente(client):
    empresa = _cabecalho_empresa(client)
    plano_original = client.get(
        '/api/v1/planos', headers=empresa
    ).get_json()['plano_atual']
    destino = 'enterprise' if plano_original != 'enterprise' else 'professional'
    try:
        alterado = client.post(
            '/api/v1/planos/alterar', headers=empresa, json={'plano': destino}
        )
        repetido = client.post(
            '/api/v1/planos/alterar', headers=empresa, json={'plano': destino}
        )
        invalido = client.post(
            '/api/v1/planos/alterar', headers=empresa, json={'plano': 'gold'}
        )
        assert alterado.status_code == 200
        assert alterado.get_json()['plano_anterior'] == plano_original
        assert alterado.get_json()['plano_atual'] == destino
        assert alterado.get_json()['repetido'] is False
        assert repetido.status_code == 200
        assert repetido.get_json()['repetido'] is True
        assert invalido.status_code == 400
    finally:
        client.post(
            '/api/v1/planos/alterar', headers=empresa,
            json={'plano': plano_original},
        )

    cidadao = {
        'Authorization': 'Bearer ' + _obter_token(
            client, 'cidadao', _CPF_CIDADAO, _SENHA_CIDADAO
        )
    }
    assert client.get('/api/v1/planos', headers=cidadao).status_code == 403
    assert client.post(
        '/api/v1/planos/alterar', headers=cidadao,
        json={'plano': 'professional'},
    ).status_code == 403


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

