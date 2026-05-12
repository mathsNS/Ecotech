"""Testes de precificação, avaliação e receita (Fases 1–4).

Cobre:
- EstadoProduto enum
- calcular_valor_avaliado (funcionando / defeito_leve / defeito_grave / sucata)
- ServicoDescarte.calcular_valor_avaliado (static, com valor_proposto)
- ServicoDescarte.validar_override
- dados.buscar_tabela_precos / buscar_preco_subcategoria
- dados.atualizar_avaliacao_solicitacao / buscar_avaliacao_solicitacao
- dados.buscar_overrides_pendentes / aprovar_override / rejeitar_override
- dados.atualizar_saldo_empresa / buscar_saldo_empresa
- dados.registrar_receita_ecotech / buscar_receita_total_ecotech
"""

import sqlite3
import pytest

from ecotech.domain.usuarios import Cidadao, Empresa
from ecotech.domain.dispositivos import Celular, Computador, Eletrodomestico, EstadoProduto
from ecotech.domain.descarte import PontoColeta
from ecotech.infrastructure.persistence.dados import Dados
from ecotech.application.services import ServicoDescarte


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dados(tmp_path, monkeypatch):
    """Banco SQLite temporário isolado por teste."""
    db_path = str(tmp_path / "test.db")
    _orig = sqlite3.connect
    monkeypatch.setattr(
        "ecotech.infrastructure.persistence.dados.sqlite3.connect",
        lambda path, **kwargs: _orig(db_path, **kwargs),
    )
    return Dados()


def _cidadao():
    return Cidadao("cid-1", "João Silva", "joao@test.com", "12345678909")

def _empresa():
    return Empresa("emp-1", "Recicla Kariri", "rk@test.com", "11222333000181",
                   "Recicla Kariri LTDA")

def _celular(subcategoria="smartphone_medio"):
    return Celular("cel-1", "Galaxy S21", 0.170, subcategoria=subcategoria)

def _ponto():
    return PontoColeta("pnt-1", "Ecoponto", "Rua A, 1", -7.2, -39.3, 500.0)


# ---------------------------------------------------------------------------
# EstadoProduto enum
# ---------------------------------------------------------------------------

def test_estado_produto_valores():
    assert EstadoProduto.FUNCIONANDO.value == "funcionando"
    assert EstadoProduto.DEFEITO_LEVE.value == "defeito_leve"
    assert EstadoProduto.DEFEITO_GRAVE.value == "defeito_grave"
    assert EstadoProduto.SUCATA.value == "sucata"


def test_estado_produto_de_string():
    assert EstadoProduto("funcionando") == EstadoProduto.FUNCIONANDO
    assert EstadoProduto("sucata") == EstadoProduto.SUCATA


def test_estado_produto_string_invalida():
    with pytest.raises(ValueError):
        EstadoProduto("perfeito")


# ---------------------------------------------------------------------------
# calcular_valor_avaliado (instância)
# ---------------------------------------------------------------------------

def test_calcular_valor_avaliado_funcionando():
    cel = _celular()
    v = cel.calcular_valor_avaliado(EstadoProduto.FUNCIONANDO, 600.0, 10.0)
    assert v == pytest.approx(600.0)


def test_calcular_valor_avaliado_defeito_leve():
    cel = _celular()
    v = cel.calcular_valor_avaliado(EstadoProduto.DEFEITO_LEVE, 600.0, 10.0)
    assert v == pytest.approx(600.0 * 0.40)


def test_calcular_valor_avaliado_defeito_grave():
    cel = _celular()
    v = cel.calcular_valor_avaliado(EstadoProduto.DEFEITO_GRAVE, 600.0, 10.0)
    assert v == pytest.approx(600.0 * 0.15)


def test_calcular_valor_avaliado_sucata_usa_valor_minimo():
    cel = _celular()
    v = cel.calcular_valor_avaliado(EstadoProduto.SUCATA, 600.0, 10.0)
    assert v == pytest.approx(10.0)


def test_calcular_valor_avaliado_sucata_nunca_negativo():
    cel = _celular()
    v = cel.calcular_valor_avaliado(EstadoProduto.SUCATA, 600.0, 0.0)
    assert v >= 0.0


# ---------------------------------------------------------------------------
# ServicoDescarte.calcular_valor_avaliado (static, com valor_proposto)
# ---------------------------------------------------------------------------

def test_servico_calcular_valor_avaliado_funcionando():
    v = ServicoDescarte.calcular_valor_avaliado("funcionando", 600.0, 10.0)
    assert v == pytest.approx(600.0)


def test_servico_calcular_valor_avaliado_defeito_leve():
    v = ServicoDescarte.calcular_valor_avaliado("defeito_leve", 600.0, 10.0)
    assert v == pytest.approx(600.0 * 0.40)


def test_servico_calcular_valor_avaliado_sucata():
    v = ServicoDescarte.calcular_valor_avaliado("sucata", 600.0, 10.0)
    assert v == pytest.approx(10.0)


def test_servico_calcular_valor_avaliado_com_proposto():
    v = ServicoDescarte.calcular_valor_avaliado("funcionando", 600.0, 10.0, valor_proposto=450.0)
    assert v == pytest.approx(450.0)


# ---------------------------------------------------------------------------
# ServicoDescarte.validar_override
# ---------------------------------------------------------------------------

def test_validar_override_dentro_do_limite():
    r = ServicoDescarte.validar_override(700.0, 600.0, 10.0)
    assert r["status"] == "aprovado"
    assert r["valor_aplicado"] == pytest.approx(700.0)


def test_validar_override_exatamente_no_cap():
    # 1.5 × 600 = 900 → aprovado (limite exato)
    r = ServicoDescarte.validar_override(900.0, 600.0, 10.0)
    assert r["status"] == "aprovado"
    assert r["valor_aplicado"] == pytest.approx(900.0)


def test_validar_override_acima_do_cap():
    r = ServicoDescarte.validar_override(1000.0, 600.0, 10.0)
    assert r["status"] == "pendente_doc"
    assert r["valor_aplicado"] == pytest.approx(900.0)  # cap aplicado


def test_validar_override_abaixo_do_minimo():
    r = ServicoDescarte.validar_override(5.0, 600.0, 10.0)
    assert r["status"] == "invalido"
    assert r["valor_aplicado"] == pytest.approx(10.0)  # minimo sucata


def test_validar_override_negativo():
    r = ServicoDescarte.validar_override(-50.0, 600.0, 10.0)
    assert r["status"] == "invalido"
    assert r["valor_aplicado"] >= 0.0


# ---------------------------------------------------------------------------
# tabela_precos (DB)
# ---------------------------------------------------------------------------

def test_tabela_precos_tem_12_subcategorias(dados):
    rows = dados.buscar_tabela_precos()
    assert len(rows) == 12


def test_buscar_preco_subcategoria_existente(dados):
    row = dados.buscar_preco_subcategoria("smartphone_medio")
    assert row is not None
    assert float(row["valor_base_funcionando"]) == pytest.approx(600.0)
    assert float(row["valor_minimo_sucata"]) == pytest.approx(10.0)


def test_buscar_preco_subcategoria_inexistente(dados):
    row = dados.buscar_preco_subcategoria("dispositivo_magico")
    assert row is None


def test_buscar_preco_iphone(dados):
    row = dados.buscar_preco_subcategoria("iphone")
    assert float(row["valor_base_funcionando"]) == pytest.approx(2500.0)


def test_buscar_preco_geladeira(dados):
    row = dados.buscar_preco_subcategoria("geladeira")
    assert float(row["valor_base_funcionando"]) == pytest.approx(900.0)


# ---------------------------------------------------------------------------
# atualizar/buscar avaliação de solicitação
# ---------------------------------------------------------------------------

@pytest.fixture
def sol_no_banco(dados):
    cid = _cidadao()
    pnt = _ponto()
    dados.salvar_cidadao(cid)
    dados.salvar_ponto(pnt)
    from ecotech.domain.descarte import SolicitacaoDescarte
    sol = SolicitacaoDescarte("sol-1", cid, pnt)
    dados.salvar_solicitacao(sol)
    return sol


def test_buscar_avaliacao_vazia_retorna_none(dados, sol_no_banco):
    row = dados.buscar_avaliacao_solicitacao("sol-1")
    # status_override deve ser 'nenhum' (default), valor_proposto nulo
    assert row is not None
    assert row["status_override"] == "nenhum"
    assert row["valor_proposto"] is None


def test_atualizar_e_buscar_avaliacao(dados, sol_no_banco):
    dados.atualizar_avaliacao_solicitacao("sol-1", "defeito_leve", 240.0, "Tela trincada", "nenhum")
    row = dados.buscar_avaliacao_solicitacao("sol-1")
    assert row["estado_produto"] == "defeito_leve"
    assert float(row["valor_proposto"]) == pytest.approx(240.0)
    assert row["justificativa_valor"] == "Tela trincada"
    assert row["status_override"] == "nenhum"


def test_atualizar_avaliacao_override_pendente(dados, sol_no_banco):
    dados.atualizar_avaliacao_solicitacao("sol-1", "funcionando", 950.0, "Valor maior justificado", "pendente_doc")
    row = dados.buscar_avaliacao_solicitacao("sol-1")
    assert row["status_override"] == "pendente_doc"


# ---------------------------------------------------------------------------
# buscar_overrides_pendentes / aprovar_override / rejeitar_override
# ---------------------------------------------------------------------------

def test_overrides_pendentes_vazio_inicialmente(dados):
    pendentes = dados.buscar_overrides_pendentes()
    assert len(pendentes) == 0


def test_aprovar_override(dados, sol_no_banco):
    dados.atualizar_avaliacao_solicitacao("sol-1", "funcionando", 950.0, "Laudo anexo", "pendente_doc")

    pendentes = dados.buscar_overrides_pendentes()
    assert len(pendentes) == 1
    assert pendentes[0]["id"] == "sol-1"

    dados.aprovar_override("sol-1")

    pendentes_apos = dados.buscar_overrides_pendentes()
    assert len(pendentes_apos) == 0

    row = dados.buscar_avaliacao_solicitacao("sol-1")
    assert row["status_override"] == "aprovado"


def test_rejeitar_override_reverte_valor(dados, sol_no_banco):
    dados.atualizar_avaliacao_solicitacao("sol-1", "funcionando", 950.0, "Valor alto", "pendente_doc")
    dados.rejeitar_override("sol-1", 600.0)

    row = dados.buscar_avaliacao_solicitacao("sol-1")
    assert row["status_override"] == "rejeitado"
    assert float(row["valor_proposto"]) == pytest.approx(600.0)


def test_override_aprovado_nao_aparece_na_fila(dados, sol_no_banco):
    dados.atualizar_avaliacao_solicitacao("sol-1", "funcionando", 950.0, "ok", "pendente_doc")
    dados.aprovar_override("sol-1")
    assert len(dados.buscar_overrides_pendentes()) == 0


# ---------------------------------------------------------------------------
# atualizar_saldo_empresa / buscar_saldo_empresa
# ---------------------------------------------------------------------------

def test_saldo_empresa_inicial_zero(dados):
    emp = _empresa()
    dados.salvar_empresa(emp, password_hash="h")
    assert dados.buscar_saldo_empresa(emp.id) == pytest.approx(0.0)


def test_atualizar_saldo_empresa_positivo(dados):
    emp = _empresa()
    dados.salvar_empresa(emp, password_hash="h")
    dados.atualizar_saldo_empresa(emp.id, 738.0)
    assert dados.buscar_saldo_empresa(emp.id) == pytest.approx(738.0)


def test_atualizar_saldo_empresa_acumulativo(dados):
    emp = _empresa()
    dados.salvar_empresa(emp, password_hash="h")
    dados.atualizar_saldo_empresa(emp.id, 738.0)
    dados.atualizar_saldo_empresa(emp.id, 765.0)
    assert dados.buscar_saldo_empresa(emp.id) == pytest.approx(1503.0)


def test_buscar_saldo_empresa_inexistente(dados):
    assert dados.buscar_saldo_empresa("nao-existe") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# registrar_receita_ecotech / buscar_receita_total_ecotech
# ---------------------------------------------------------------------------

def test_receita_ecotech_inicial_zero(dados):
    assert dados.buscar_receita_total_ecotech() == pytest.approx(0.0)


def test_registrar_receita_ecotech(dados, sol_no_banco):
    dados.registrar_receita_ecotech("sol-1", 72.0)
    assert dados.buscar_receita_total_ecotech() == pytest.approx(72.0)


def test_receita_ecotech_acumulativa(dados, sol_no_banco):
    dados.registrar_receita_ecotech("sol-1", 72.0)
    dados.registrar_receita_ecotech("sol-1", 45.0)
    assert dados.buscar_receita_total_ecotech() == pytest.approx(117.0)


def test_historico_receita_ecotech_ordenado(dados, sol_no_banco):
    dados.registrar_receita_ecotech("sol-1", 72.0)
    dados.registrar_receita_ecotech("sol-1", 18.0)
    hist = dados.buscar_historico_receita_ecotech()
    assert len(hist) == 2


# ---------------------------------------------------------------------------
# TAXAS_ECOTECH constante
# ---------------------------------------------------------------------------

def test_taxas_ecotech_free():
    assert ServicoDescarte.TAXAS_ECOTECH["free"] == pytest.approx(0.08)

def test_taxas_ecotech_professional():
    assert ServicoDescarte.TAXAS_ECOTECH["professional"] == pytest.approx(0.05)

def test_taxas_ecotech_enterprise():
    assert ServicoDescarte.TAXAS_ECOTECH["enterprise"] == pytest.approx(0.02)

def test_soma_parcelas_free():
    t = ServicoDescarte.TAXAS_ECOTECH["free"]
    cidadao = 0.10
    empresa = 1.0 - cidadao - t
    assert cidadao + t + empresa == pytest.approx(1.0)

def test_empresa_fica_mais_em_enterprise():
    free_empresa = 1.0 - 0.10 - ServicoDescarte.TAXAS_ECOTECH["free"]
    ent_empresa = 1.0 - 0.10 - ServicoDescarte.TAXAS_ECOTECH["enterprise"]
    assert ent_empresa > free_empresa
