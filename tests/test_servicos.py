import pytest
from datetime import datetime
from unittest.mock import Mock

from ecotech.application.factories import EstadoFactory
from ecotech.application.services import ServicoDescarte, ServicoRelatorio
from ecotech.domain.usuarios import Cidadao, Empresa, Administrador
from ecotech.domain.relatorio import RelatorioAmbiental
from ecotech.domain.descarte import SolicitacaoDescarte, ItemDescarte
from ecotech.domain.estados import Solicitado, Coletado, Reciclado, Reutilizado, Descartado, Cancelado
from ecotech.application.factories import DispositivoFactory


# ---- EstadoFactory ----

class TestEstadoFactory:

    def test_solicitado(self):
        estado = EstadoFactory.criar_do_banco('SOLICITADO')
        assert isinstance(estado, Solicitado)

    def test_coletado(self):
        assert isinstance(EstadoFactory.criar_do_banco('COLETADO'), Coletado)

    def test_reciclado(self):
        assert isinstance(EstadoFactory.criar_do_banco('RECICLADO'), Reciclado)

    def test_reutilizado(self):
        assert isinstance(EstadoFactory.criar_do_banco('REUTILIZADO'), Reutilizado)

    def test_descartado(self):
        assert isinstance(EstadoFactory.criar_do_banco('DESCARTADO'), Descartado)

    def test_cancelado(self):
        assert isinstance(EstadoFactory.criar_do_banco('CANCELADO'), Cancelado)

    def test_estado_desconhecido_retorna_solicitado(self):
        estado = EstadoFactory.criar_do_banco('ESTADO_INEXISTENTE')
        assert isinstance(estado, Solicitado)

    def test_cada_chamada_retorna_nova_instancia(self):
        e1 = EstadoFactory.criar_do_banco('RECICLADO')
        e2 = EstadoFactory.criar_do_banco('RECICLADO')
        assert e1 is not e2


# ---- Guard criar_solicitacao ----

class TestGuardCriarSolicitacao:

    def test_cidadao_ativo_pode_criar(self):
        servico = ServicoDescarte()
        cidadao = Cidadao("1", "João", "joao@test.com", "12345678909")
        sol = servico.criar_solicitacao(cidadao)
        assert sol is not None

    def test_empresa_ativa_pode_criar(self):
        servico = ServicoDescarte()
        empresa = Empresa("2", "Recicla", "r@test.com", "11222333000181", "Recicla Ltda")
        sol = servico.criar_solicitacao(empresa)
        assert sol is not None

    def test_usuario_inativo_levanta_valueerror(self):
        servico = ServicoDescarte()
        cidadao = Cidadao("3", "Inativo", "i@test.com", "12345678909")
        cidadao.desativar()
        with pytest.raises(ValueError, match="nao pode realizar descarte"):
            servico.criar_solicitacao(cidadao)

    def test_empresa_com_limite_excedido_levanta_valueerror(self):
        servico = ServicoDescarte()
        empresa = Empresa("4", "Cheia", "c@test.com", "11222333000181", "Cheia Ltda")
        # preenche o limite completamente
        empresa.registrar_descarte(empresa.limite_mensal)
        with pytest.raises(ValueError, match="nao pode realizar descarte"):
            servico.criar_solicitacao(empresa)

    def test_solicitacao_adicionada_ao_cache(self):
        servico = ServicoDescarte()
        cidadao = Cidadao("5", "Maria", "m@test.com", "12345678909")
        sol = servico.criar_solicitacao(cidadao)
        assert servico.obter_solicitacao(sol.id) is sol


# ---- Filtro por data em gerar_relatorio_periodo ----

def _criar_solicitacao_com_data(data_str: str) -> SolicitacaoDescarte:
    cidadao = Cidadao("x", "Teste", "t@test.com", "12345678909")
    sol = SolicitacaoDescarte("sol-" + data_str, cidadao, None)
    sol._data_criacao = datetime.strptime(data_str, "%d/%m/%Y %H:%M")
    return sol


class TestServicoRelatorioFiltroData:

    def setup_method(self):
        self.servico = ServicoRelatorio()
        self.sol_jan = _criar_solicitacao_com_data("10/01/2025 10:00")
        self.sol_mar = _criar_solicitacao_com_data("15/03/2025 10:00")
        self.sol_jun = _criar_solicitacao_com_data("20/06/2025 10:00")
        self.todas = [self.sol_jan, self.sol_mar, self.sol_jun]

    def test_sem_filtro_inclui_todas(self):
        rel = self.servico.gerar_relatorio_periodo("geral", self.todas)
        assert rel.gerar_relatorio()["total_solicitacoes"] == 3

    def test_data_inicio_exclui_anteriores(self):
        inicio = datetime(2025, 2, 1)
        rel = self.servico.gerar_relatorio_periodo("periodo", self.todas, data_inicio=inicio)
        assert rel.gerar_relatorio()["total_solicitacoes"] == 2

    def test_data_fim_exclui_posteriores(self):
        fim = datetime(2025, 4, 1)
        rel = self.servico.gerar_relatorio_periodo("periodo", self.todas, data_fim=fim)
        assert rel.gerar_relatorio()["total_solicitacoes"] == 2

    def test_intervalo_exato(self):
        inicio = datetime(2025, 2, 1)
        fim = datetime(2025, 5, 1)
        rel = self.servico.gerar_relatorio_periodo("periodo", self.todas, data_inicio=inicio, data_fim=fim)
        assert rel.gerar_relatorio()["total_solicitacoes"] == 1

    def test_intervalo_sem_resultados(self):
        inicio = datetime(2025, 8, 1)
        rel = self.servico.gerar_relatorio_periodo("vazio", self.todas, data_inicio=inicio)
        assert rel.gerar_relatorio()["total_solicitacoes"] == 0


# ---- calcular_eficiencia_reciclagem ----

def _sol_com_estado(estado, peso_kg: float) -> SolicitacaoDescarte:
    cidadao = Cidadao("u", "Usr", "u@t.com", "12345678909")
    celular = DispositivoFactory.criar_celular("d", "Dev", peso_kg)
    sol = SolicitacaoDescarte("s-" + str(id(estado)), cidadao, None)
    sol._estado = estado
    item = ItemDescarte(celular, 1, "")
    sol._itens.append(item)
    return sol


class TestCalcularEficienciaReciclagem:

    def test_sem_solicitacoes_retorna_zero(self):
        rel = RelatorioAmbiental("vazio")
        assert rel.calcular_eficiencia_reciclagem() == 0.0

    def test_cem_porcento_reciclado(self):
        rel = RelatorioAmbiental("r")
        rel.adicionar_solicitacao(_sol_com_estado(Reciclado(), 2.0))
        rel.adicionar_solicitacao(_sol_com_estado(Reciclado(), 3.0))
        assert rel.calcular_eficiencia_reciclagem() == 100.0

    def test_cem_porcento_reutilizado(self):
        rel = RelatorioAmbiental("r")
        rel.adicionar_solicitacao(_sol_com_estado(Reutilizado(), 5.0))
        assert rel.calcular_eficiencia_reciclagem() == 100.0

    def test_cinquenta_porcento(self):
        rel = RelatorioAmbiental("r")
        rel.adicionar_solicitacao(_sol_com_estado(Reciclado(), 1.0))
        rel.adicionar_solicitacao(_sol_com_estado(Descartado(), 1.0))
        assert rel.calcular_eficiencia_reciclagem() == 50.0

    def test_solicitacoes_nao_finalizadas_nao_contam(self):
        # Solicitado e Coletado não entram no denominador
        rel = RelatorioAmbiental("r")
        rel.adicionar_solicitacao(_sol_com_estado(Solicitado(), 10.0))
        rel.adicionar_solicitacao(_sol_com_estado(Coletado(), 10.0))
        assert rel.calcular_eficiencia_reciclagem() == 0.0

    def test_misto_reciclado_reutilizado_descartado(self):
        rel = RelatorioAmbiental("r")
        rel.adicionar_solicitacao(_sol_com_estado(Reciclado(), 2.0))
        rel.adicionar_solicitacao(_sol_com_estado(Reutilizado(), 2.0))
        rel.adicionar_solicitacao(_sol_com_estado(Descartado(), 1.0))
        # (2+2) / 5 = 80%
        assert rel.calcular_eficiencia_reciclagem() == 80.0

    def test_resultado_incluido_no_gerar_relatorio(self):
        rel = RelatorioAmbiental("r")
        rel.adicionar_solicitacao(_sol_com_estado(Reciclado(), 1.0))
        dados = rel.gerar_relatorio()
        assert "eficiencia_reciclagem_pct" in dados
        assert dados["eficiencia_reciclagem_pct"] == 100.0
