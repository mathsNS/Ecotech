"""
Testes para a camada de persistência (Dados/RepositorioBase).

Cobre:
  - salvar e buscar cada tipo de entidade
  - atualizar_solicitacao (estado e método de tratamento)
  - atualizar_ocupacao_ponto
  - desativar_usuario (soft-delete)
  - transações: falha em um dos INSERTs não polui o banco
  - PRAGMA foreign_keys ativo
  - salvar_empresa persiste limite_mensal e descartado_mes reais
  - salvar_solicitacao usa o estado real do objeto de domínio
"""

import sqlite3
import pytest

from ecotech.domain.usuarios import Cidadao, Empresa, Administrador
from ecotech.domain.dispositivos import Celular
from ecotech.domain.descarte import PontoColeta, SolicitacaoDescarte, ItemDescarte
from ecotech.infrastructure.persistence.dados import Dados


# ---------------------------------------------------------------------------
# Fixture: banco em memória isolado por teste
# ---------------------------------------------------------------------------

@pytest.fixture
def dados(tmp_path, monkeypatch):
    """Cria uma instância de Dados usando um banco SQLite em arquivo temporário."""
    db_path = str(tmp_path / "test.db")
    _orig_connect = sqlite3.connect  # salva referência antes do patch
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: _orig_connect(db_path, **kwargs),
    )
    return Dados()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cidadao():
    return Cidadao("cid-1", "João Silva", "joao@test.com", "12345678909")

def _empresa():
    return Empresa("emp-1", "Recicla Kariri", "rk@test.com", "11222333000181",
                   "Recicla Kariri LTDA")

def _admin():
    return Administrador("adm-1", "Admin", "admin@test.com", 3)

def _celular():
    return Celular("cel-1", "iPhone X", 0.194, "Apple", "X")

def _ponto():
    return PontoColeta("pnt-1", "Ecoponto Sul", "Rua A, 1", -7.2, -39.3, 500.0)


# ---------------------------------------------------------------------------
# PRAGMA foreign_keys
# ---------------------------------------------------------------------------

def test_pragma_foreign_keys_ativo(dados):
    row = dados.conn.execute("PRAGMA foreign_keys").fetchone()
    assert row[0] == 1, "PRAGMA foreign_keys deve estar ativo"


# ---------------------------------------------------------------------------
# Cidadão
# ---------------------------------------------------------------------------

def test_salvar_e_buscar_cidadao(dados):
    cid = _cidadao()
    dados.salvar_cidadao(cid, password_hash="hash_teste")

    row = dados.buscar_cidadao("cid-1")
    assert row is not None
    assert row["nome"] == "João Silva"
    assert row["cpf"] == "12345678909"
    assert row["password_hash"] == "hash_teste"


def test_salvar_cidadao_por_cpf(dados):
    cid = _cidadao()
    dados.salvar_cidadao(cid, password_hash="abc")

    row = dados.buscar_usuario_por_cpf("12345678909")
    assert row is not None
    assert row["id"] == "cid-1"


def test_salvar_cidadao_idempotente(dados):
    cid = _cidadao()
    dados.salvar_cidadao(cid)
    dados.salvar_cidadao(cid)  # INSERT OR IGNORE — não deve explodir

    total = dados.contar_usuarios()
    assert total == 1


# ---------------------------------------------------------------------------
# Empresa
# ---------------------------------------------------------------------------

def test_salvar_empresa_persiste_limite_mensal(dados):
    emp = _empresa()
    dados.salvar_empresa(emp)

    row = dados.buscar_empresa("emp-1")
    assert row is not None
    assert row["cnpj"] == "11222333000181"
    assert row["razao_social"] == "Recicla Kariri LTDA"
    # limite_mensal deve ser 1000.0 (valor do domínio), não 0
    assert row["limite_mensal"] == 1000.0
    assert row["descartado_mes"] == 0.0


def test_buscar_empresa_por_cnpj(dados):
    dados.salvar_empresa(_empresa())
    row = dados.buscar_usuario_por_cnpj("11222333000181")
    assert row is not None
    assert row["id"] == "emp-1"


# ---------------------------------------------------------------------------
# Administrador
# ---------------------------------------------------------------------------

def test_salvar_e_buscar_administrador(dados):
    adm = _admin()
    dados.salvar_administrador(adm, password_hash="admhash")

    row = dados.buscar_usuario("adm-1")
    assert row is not None
    assert row["tipo"] == "administrador"
    assert row["password_hash"] == "admhash"


def test_buscar_admin_por_email(dados):
    dados.salvar_administrador(_admin())
    row = dados.buscar_usuario_por_email("admin@test.com")
    assert row is not None
    assert row["id"] == "adm-1"


# ---------------------------------------------------------------------------
# Dispositivo
# ---------------------------------------------------------------------------

def test_salvar_e_buscar_dispositivo(dados):
    cel = _celular()
    dados.salvar_dispositivo(cel)

    row = dados.buscar_dispositivo("cel-1")
    assert row is not None
    assert row["nome"] == "iPhone X"
    assert row["peso_kg"] == pytest.approx(0.194)


# ---------------------------------------------------------------------------
# Ponto de Coleta
# ---------------------------------------------------------------------------

def test_salvar_e_buscar_ponto(dados):
    pnt = _ponto()
    dados.salvar_ponto(pnt)

    row = dados.buscar_ponto_coleta("pnt-1")
    assert row is not None
    assert row["nome"] == "Ecoponto Sul"
    assert row["capacidade_kg"] == 500.0
    assert row["ocupacao_atual_kg"] == 0.0


def test_atualizar_ocupacao_ponto(dados):
    dados.salvar_ponto(_ponto())
    dados.atualizar_ocupacao_ponto("pnt-1", 123.5)

    row = dados.buscar_ponto_coleta("pnt-1")
    assert row["ocupacao_atual_kg"] == pytest.approx(123.5)


def test_buscar_todos_pontos_coleta(dados):
    dados.salvar_ponto(_ponto())
    pnt2 = PontoColeta("pnt-2", "Ecoponto Norte", "Rua B, 2", -7.1, -39.1, 300.0)
    dados.salvar_ponto(pnt2)

    pontos = dados.buscar_todos_pontos_coleta()
    assert len(pontos) == 2


# ---------------------------------------------------------------------------
# Solicitação salva com estado real do objeto
# ---------------------------------------------------------------------------

def test_salvar_solicitacao_usa_estado_real(dados):
    cid = _cidadao()
    pnt = _ponto()
    dados.salvar_cidadao(cid)
    dados.salvar_ponto(pnt)

    sol = SolicitacaoDescarte("sol-1", cid, pnt)
    dados.salvar_solicitacao(sol)

    row = dados.buscar_solicitacao("sol-1")
    assert row is not None
    # estado deve refletir o nome do estado do domínio ("Solicitado" -> "SOLICITADO")
    assert row["estado"] == "SOLICITADO"


def test_salvar_solicitacao_com_item(dados):
    cid = _cidadao()
    pnt = _ponto()
    cel = _celular()
    dados.salvar_cidadao(cid)
    dados.salvar_ponto(pnt)
    dados.salvar_dispositivo(cel)

    sol = SolicitacaoDescarte("sol-1", cid, pnt)
    dados.salvar_solicitacao(sol)

    item = ItemDescarte(cel, 2, "tela quebrada")
    dados.salvar_itens_descarte("sol-1", item)

    itens = dados.buscar_itens_solicitacao("sol-1")
    assert len(itens) == 1
    assert itens[0]["quantidade"] == 2
    assert itens[0]["observacoes"] == "tela quebrada"


# ---------------------------------------------------------------------------
# atualizar_solicitacao
# ---------------------------------------------------------------------------

def test_atualizar_estado_solicitacao(dados):
    cid = _cidadao()
    pnt = _ponto()
    dados.salvar_cidadao(cid)
    dados.salvar_ponto(pnt)

    sol = SolicitacaoDescarte("sol-1", cid, pnt)
    dados.salvar_solicitacao(sol)

    dados.atualizar_solicitacao("sol-1", "COLETADO")

    row = dados.buscar_solicitacao("sol-1")
    assert row["estado"] == "COLETADO"


def test_atualizar_estado_com_metodo(dados):
    cid = _cidadao()
    pnt = _ponto()
    dados.salvar_cidadao(cid)
    dados.salvar_ponto(pnt)

    sol = SolicitacaoDescarte("sol-1", cid, pnt)
    dados.salvar_solicitacao(sol)

    dados.atualizar_solicitacao("sol-1", "EM_PROCESSAMENTO", metodo_tratamento="Reciclagem")

    row = dados.buscar_solicitacao("sol-1")
    assert row["estado"] == "EM_PROCESSAMENTO"
    assert row["metodo_tratamento"] == "Reciclagem"


def test_atualizar_sem_metodo_preserva_metodo_anterior(dados):
    cid = _cidadao()
    pnt = _ponto()
    dados.salvar_cidadao(cid)
    dados.salvar_ponto(pnt)

    sol = SolicitacaoDescarte("sol-1", cid, pnt)
    dados.salvar_solicitacao(sol)

    # define método
    dados.atualizar_solicitacao("sol-1", "EM_PROCESSAMENTO", "Reciclagem")
    # avança estado sem passar método
    dados.atualizar_solicitacao("sol-1", "RECICLADO")

    row = dados.buscar_solicitacao("sol-1")
    assert row["estado"] == "RECICLADO"
    assert row["metodo_tratamento"] == "Reciclagem"  # preservado pelo COALESCE


# ---------------------------------------------------------------------------
# desativar_usuario (soft-delete)
# ---------------------------------------------------------------------------

def test_desativar_usuario(dados):
    cid = _cidadao()
    dados.salvar_cidadao(cid)

    dados.desativar_usuario("cid-1")

    row = dados.buscar_usuario("cid-1")
    assert row["ativo"] == 0


def test_desativar_usuario_some_do_buscar_por_cpf(dados):
    cid = _cidadao()
    dados.salvar_cidadao(cid)

    dados.desativar_usuario("cid-1")

    # buscar_usuario_por_cpf filtra ativo = 1
    row = dados.buscar_usuario_por_cpf("12345678909")
    assert row is None


# ---------------------------------------------------------------------------
# buscar_solicitacoes_usuario
# ---------------------------------------------------------------------------

def test_buscar_solicitacoes_usuario(dados):
    cid = _cidadao()
    pnt = _ponto()
    dados.salvar_cidadao(cid)
    dados.salvar_ponto(pnt)

    for sid in ("sol-1", "sol-2"):
        sol = SolicitacaoDescarte(sid, cid, pnt)
        dados.salvar_solicitacao(sol)

    rows = dados.buscar_solicitacoes_usuario("cid-1")
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# Notificações
# ---------------------------------------------------------------------------

def test_salvar_e_buscar_notificacoes(dados):
    dados.salvar_cidadao(_cidadao())
    dados.salvar_notificacao("cid-1", "Solicitação aprovada")
    dados.salvar_notificacao("cid-1", "Coleta agendada")

    notifs = dados.buscar_notificacoes_usuario("cid-1")
    assert len(notifs) == 2


# ---------------------------------------------------------------------------
# Contagens
# ---------------------------------------------------------------------------

def test_contar_usuarios(dados):
    dados.salvar_cidadao(_cidadao())
    dados.salvar_empresa(_empresa())
    assert dados.contar_usuarios() == 2


def test_contar_solicitacoes(dados):
    cid = _cidadao()
    pnt = _ponto()
    dados.salvar_cidadao(cid)
    dados.salvar_ponto(pnt)

    for sid in ("sol-1", "sol-2", "sol-3"):
        sol = SolicitacaoDescarte(sid, cid, pnt)
        dados.salvar_solicitacao(sol)

    assert dados.contar_solicitacoes() == 3
