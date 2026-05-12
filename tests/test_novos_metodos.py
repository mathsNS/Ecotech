"""Testes para os métodos adicionados nesta sessão:
- dados.buscar_plano_empresa
- dados.atualizar_plano_empresa
- dados.atualizar_usuario
- servico.calcular_metricas (co2 / taxa reciclagem)
- MetodoTratamentoFactory
"""

import sqlite3
import pytest

from ecotech.domain.usuarios import Cidadao, Empresa
from ecotech.domain.dispositivos import Celular
from ecotech.domain.descarte import PontoColeta, SolicitacaoDescarte
from ecotech.application.factories import MetodoTratamentoFactory
from ecotech.infrastructure.persistence.dados import Dados
from ecotech.application.services import ServicoDescarte


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def dados(tmp_path, monkeypatch):
    """Banco SQLite temporário isolado por teste."""
    db_path = str(tmp_path / "test.db")
    _orig_connect = sqlite3.connect
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: _orig_connect(db_path, **kwargs),
    )
    return Dados()


def _empresa():
    return Empresa("emp-1", "Recicla Kariri", "rk@test.com", "11222333000181",
                   "Recicla Kariri LTDA")

def _cidadao():
    return Cidadao("cid-1", "João Silva", "joao@test.com", "12345678909")

def _celular():
    return Celular("cel-1", "iPhone X", 0.194, "Apple", "X")

def _ponto():
    return PontoColeta("pnt-1", "Ecoponto Sul", "Rua A, 1", -7.2, -39.3, 500.0)


# ---------------------------------------------------------------------------
# buscar_plano_empresa / atualizar_plano_empresa
# ---------------------------------------------------------------------------

def test_plano_padrao_e_free(dados):
    """Empresa recém-criada tem plano 'free'."""
    emp = _empresa()
    dados.salvar_empresa(emp, password_hash='hash')
    assert dados.buscar_plano_empresa(emp.id) == 'free'


def test_atualizar_plano_para_professional(dados):
    emp = _empresa()
    dados.salvar_empresa(emp, password_hash='hash')
    dados.atualizar_plano_empresa(emp.id, 'professional')
    assert dados.buscar_plano_empresa(emp.id) == 'professional'


def test_atualizar_plano_para_enterprise(dados):
    emp = _empresa()
    dados.salvar_empresa(emp, password_hash='hash')
    dados.atualizar_plano_empresa(emp.id, 'enterprise')
    assert dados.buscar_plano_empresa(emp.id) == 'enterprise'


def test_atualizar_plano_invalido_levanta_valueerror(dados):
    emp = _empresa()
    dados.salvar_empresa(emp, password_hash='hash')
    with pytest.raises(ValueError):
        dados.atualizar_plano_empresa(emp.id, 'gold')


def test_buscar_plano_usuario_inexistente_retorna_free(dados):
    """ID inexistente retorna 'free' sem erro."""
    assert dados.buscar_plano_empresa('id-inexistente') == 'free'


# ---------------------------------------------------------------------------
# atualizar_usuario
# ---------------------------------------------------------------------------

def test_atualizar_nome_e_email(dados):
    cid = _cidadao()
    dados.salvar_cidadao(cid, password_hash='hash')
    dados.atualizar_usuario(cid.id, 'João Atualizado', 'novo@email.com')
    row = dados.buscar_usuario(cid.id)
    assert row['nome'] == 'João Atualizado'
    assert row['email'] == 'novo@email.com'


def test_atualizar_usuario_sem_senha_nao_altera_hash(dados):
    from werkzeug.security import generate_password_hash
    cid = _cidadao()
    hash_original = generate_password_hash('senha123')
    dados.salvar_cidadao(cid, password_hash=hash_original)

    dados.atualizar_usuario(cid.id, 'Novo Nome', 'novo@email.com', password_hash=None)
    row = dados.buscar_usuario(cid.id)
    assert row['password_hash'] == hash_original


def test_atualizar_usuario_com_nova_senha(dados):
    from werkzeug.security import generate_password_hash, check_password_hash
    cid = _cidadao()
    dados.salvar_cidadao(cid, password_hash=generate_password_hash('senhaAntiga'))

    novo_hash = generate_password_hash('novaSenha456')
    dados.atualizar_usuario(cid.id, cid.nome, cid.email, password_hash=novo_hash)
    row = dados.buscar_usuario(cid.id)
    assert check_password_hash(row['password_hash'], 'novaSenha456')


# ---------------------------------------------------------------------------
# MetodoTratamentoFactory
# ---------------------------------------------------------------------------

def test_factory_criar_reciclagem():
    m = MetodoTratamentoFactory.criar_reciclagem()
    assert m.obter_nome() == 'Reciclagem'


def test_factory_criar_reuso():
    m = MetodoTratamentoFactory.criar_reuso()
    assert m.obter_nome() == 'Reuso'


def test_factory_criar_descarte_seguro():
    m = MetodoTratamentoFactory.criar_descarte_controlado()
    assert m.obter_nome() == 'Descarte Controlado'


# ---------------------------------------------------------------------------
# calcular_metricas - pontos e CO2
# ---------------------------------------------------------------------------

@pytest.fixture
def servico_com_solicitacao():
    """Retorna (servico, solicitacao) com 1 item reciclado de 2 kg."""
    cid = _cidadao()
    cel = _celular()
    pnt = _ponto()

    servico = ServicoDescarte()

    sol = servico.criar_solicitacao(cid, pnt)
    servico.adicionar_item_solicitacao(sol, cel, 1)

    # avança até Reciclado
    servico.avancar_estado_solicitacao(sol)  # → Coletado
    servico.avancar_estado_solicitacao(sol)  # → EmProcessamento
    metodo = MetodoTratamentoFactory.criar_reciclagem()
    servico.definir_metodo_tratamento(sol, metodo)
    servico.avancar_estado_solicitacao(sol)  # → Reciclado

    return servico, sol


def test_calcular_metricas_pontos(servico_com_solicitacao):
    servico, sol = servico_com_solicitacao
    metricas = servico.calcular_metricas([sol])
    # 10 pts/kg × peso_total; deve ser > 0
    assert metricas['pontos'] > 0


def test_calcular_metricas_peso_total(servico_com_solicitacao):
    servico, sol = servico_com_solicitacao
    metricas = servico.calcular_metricas([sol])
    assert metricas['peso_total'] > 0


def test_calcular_metricas_total_processadas(servico_com_solicitacao):
    servico, sol = servico_com_solicitacao
    metricas = servico.calcular_metricas([sol])
    assert metricas['total_processadas'] == 1
