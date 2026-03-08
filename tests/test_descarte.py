import pytest

from ecotech.domain.descarte import (
    ItemDescarte,
    PontoColeta,
    SolicitacaoDescarte,
    RastreamentoEntrega
)

# ------
# MOCKS
# ------

class MockDispositivo:
    def __init__(self, nome = "Celular", peso_kg = 0.2, impacto = 5):
        self.nome = nome
        self.peso_kg = peso_kg
        self._impacto = impacto

    def calcular_impacto_ambiental(self):
        return self._impacto
    
class MockUsuario:
    def __init__(self, nome="Maria"):
        self.nome = nome

class MockEstado:
    def avancar(self, solicitacao):
        return self

    def obter_nome(self):
        return "MockEstado"

    def pode_cancelar(self):
        return True

# -------------------------------
# TESTES RASTREAMENTO DE ENTREGA
# -------------------------------

def test_rastreamento_criacao():
    rastreio = RastreamentoEntrega("R-1")

    assert rastreio.id_rastreio == "R-1"
    assert len(rastreio.historico) == 1
    assert "Solicitação iniciada" in rastreio.historico[0]

def test_rastreamento_atualizar_status():
    rastreio = RastreamentoEntrega("R-2")
    rastreio.atualizar_status("Em transporte")

    assert len(rastreio.historico) == 2
    assert "Em transporte" in rastreio.historico[-1]

# ----------------------
# TESTES ITEM DESCARTE
# ----------------------

def test_item_descarte_criacao():
    dispositivo = MockDispositivo()
    item = ItemDescarte(dispositivo, quantidade = 2)

    assert item.quantidade == 2
    assert item.dispositivo.nome == "Celular"

def test_item_descarte_quantidade_invalida():
    dispositivo = MockDispositivo()

    with pytest.raises(ValueError):
        ItemDescarte(dispositivo, quantidade = 0)

def test_calculo_peso_total():
    dispositivo = MockDispositivo(peso_kg = 1)
    item = ItemDescarte(dispositivo, quantidade = 3)

    assert item.calcular_peso_total() == 3

def test_calculo_impacto_total():
    dispositivo = MockDispositivo(impacto = 10)
    item = ItemDescarte(dispositivo, quantidade = 2)

    assert item.calcular_impacto_total() == 20

# ------------------------
# TESTES PONTO DE COLETA
# ------------------------

def test_ponto_coleta_receber():
    ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3, capacidade_kg = 100)

    ponto.validar_e_receber(20)

    assert ponto.ocupacao_atual_kg == 20

def test_ponto_coleta_excede_capacidade():
    ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3, capacidade_kg = 50)

    with pytest.raises(ValueError):
        ponto.validar_e_receber(100)

def test_disponibilidade_percentual():
    ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3, capacidade_kg=100)

    ponto.adicionar_ocupacao(50)

    assert ponto.calcular_disponibilidade_percentual() == 50.0

# -------------------------------
# TESTES SOLICITAÇÃO DE DESCARTE
# -------------------------------

def test_criar_solicitacao():
    usuario = MockUsuario()
    solicitacao = SolicitacaoDescarte("1", usuario)

    assert solicitacao.id == "1"
    assert solicitacao.usuario.nome == "Maria"

def test_adicionar_item():
    usuario = MockUsuario()
    dispositivo = MockDispositivo(peso_kg=1)

    solicitacao = SolicitacaoDescarte("1", usuario)
    item = ItemDescarte(dispositivo, quantidade=2)

    solicitacao.adicionar_item(item)

    assert len(solicitacao.itens) == 1

def test_calcular_peso_total_solicitacao():
    usuario = MockUsuario()

    d1 = MockDispositivo(peso_kg=1)
    d2 = MockDispositivo(peso_kg=2)

    solicitacao = SolicitacaoDescarte("1", usuario)

    solicitacao.adicionar_item(ItemDescarte(d1, 2))
    solicitacao.adicionar_item(ItemDescarte(d2, 1))

    assert solicitacao.calcular_peso_total() == 4

def test_cancelar_solicitacao():
    usuario = MockUsuario()
    solicitacao = SolicitacaoDescarte("1", usuario)

    solicitacao.cancelar("Erro no pedido")

    assert "Cancelado" in solicitacao.rastreamento.historico[-1]

def test_obter_resumo():
    usuario = MockUsuario()
    solicitacao = SolicitacaoDescarte("1", usuario)

    resumo = solicitacao.obter_resumo()

    assert resumo["id"] == "1"
    assert resumo["usuario"] == "Maria"