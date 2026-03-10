"""Testes para os Mixins de herança múltipla (LoggableMixin e NotificavelMixin)."""

import pytest
from ecotech.domain.mixins import LoggableMixin, NotificavelMixin
from ecotech.domain.descarte import PontoColeta, SolicitacaoDescarte
from ecotech.domain.usuarios import Cidadao


# ---------------------------------
# TESTES LoggableMixin via PontoColeta
# ---------------------------------

class TestLoggableMixin:
    """Testes para o LoggableMixin aplicado ao PontoColeta."""

    def test_log_criacao_automatico(self):
        """Verifica que log é registrado automaticamente ao criar PontoColeta."""
        ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3)
        assert len(ponto.log_registros) == 1
        assert ponto.log_registros[0]["acao"] == "Ponto de coleta criado"

    def test_log_adicionar_ocupacao(self):
        """Verifica que adicionar ocupação registra entrada no log."""
        ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3, 100.0)
        ponto.adicionar_ocupacao(25.0)
        assert len(ponto.log_registros) == 2
        assert "Ocupação adicionada" in ponto.log_registros[1]["acao"]
        assert "+25.0kg" in ponto.log_registros[1]["detalhe"]

    def test_ultimo_log(self):
        """Verifica que ultimo_log retorna a entrada mais recente."""
        ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3)
        ponto.adicionar_ocupacao(10.0)
        ultimo = ponto.ultimo_log
        assert ultimo["acao"] == "Ocupação adicionada"

    def test_limpar_log(self):
        """Verifica que limpar_log remove todas as entradas."""
        ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3)
        ponto.adicionar_ocupacao(10.0)
        ponto.limpar_log()
        assert len(ponto.log_registros) == 0

    def test_log_copia_defensiva(self):
        """Verifica que log_registros retorna cópia (não referência direta)."""
        ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3)
        registros = ponto.log_registros
        registros.clear()
        assert len(ponto.log_registros) == 1

    def test_ultimo_log_vazio(self):
        """Verifica que ultimo_log retorna dict vazio quando log está limpo."""
        ponto = PontoColeta("1", "EcoPonto", "Rua A", -7.2, -39.3)
        ponto.limpar_log()
        assert ponto.ultimo_log == {}


# -----------------------------------------
# TESTES NotificavelMixin via SolicitacaoDescarte
# -----------------------------------------

class TestNotificavelMixin:
    """Testes para o NotificavelMixin aplicado ao SolicitacaoDescarte."""

    def _criar_solicitacao(self):
        """Helper para criar solicitação de teste."""
        cidadao = Cidadao("1", "Maria", "maria@email.com", "12345678901")
        return SolicitacaoDescarte("SOL-1", cidadao)

    def test_emitir_notificacao(self):
        """Verifica que notificações são emitidas corretamente."""
        sol = self._criar_solicitacao()
        sol.emitir_notificacao("Teste", "Mensagem de teste")
        assert sol.total_nao_lidas >= 1

    def test_notificacao_prioridade_invalida(self):
        """Verifica validação de prioridade inválida."""
        sol = self._criar_solicitacao()
        with pytest.raises(ValueError, match="Prioridade"):
            sol.emitir_notificacao("Teste", "Msg", prioridade="urgente")

    def test_marcar_como_lida(self):
        """Verifica que notificações podem ser marcadas como lidas."""
        sol = self._criar_solicitacao()
        sol.emitir_notificacao("Teste", "Msg")
        nao_lidas_antes = sol.total_nao_lidas
        sol.marcar_todas_como_lidas()
        assert sol.total_nao_lidas == 0
        assert nao_lidas_antes > 0

    def test_marcar_indice_invalido(self):
        """Verifica exceção ao marcar índice fora do intervalo."""
        sol = self._criar_solicitacao()
        with pytest.raises(IndexError):
            sol.marcar_como_lida(999)

    def test_limpar_notificacoes_lidas(self):
        """Verifica remoção de notificações já lidas."""
        sol = self._criar_solicitacao()
        sol.emitir_notificacao("A", "Msg A")
        sol.emitir_notificacao("B", "Msg B")
        sol.marcar_como_lida(0)
        sol.limpar_notificacoes_lidas()
        pendentes = sol.notificacoes_pendentes
        assert len(pendentes) >= 1


# -----------------------------------------
# TESTES herança múltipla (ambos Mixins)
# -----------------------------------------

class TestHerancaMultipla:
    """Testes que verificam a coexistência dos dois Mixins na mesma classe."""

    def test_solicitacao_tem_ambos_mixins(self):
        """Verifica que SolicitacaoDescarte herda de ambos os Mixins."""
        assert issubclass(SolicitacaoDescarte, LoggableMixin)
        assert issubclass(SolicitacaoDescarte, NotificavelMixin)

    def test_ponto_coleta_herda_loggable(self):
        """Verifica que PontoColeta herda de LoggableMixin."""
        assert issubclass(PontoColeta, LoggableMixin)

    def test_log_e_notificacao_independentes(self):
        """Verifica que log e notificações operam de forma independente."""
        cidadao = Cidadao("1", "Maria", "maria@email.com", "12345678901")
        sol = SolicitacaoDescarte("SOL-1", cidadao)

        qtd_logs_inicial = len(sol.log_registros)
        sol.emitir_notificacao("Extra", "Notificação manual")
        assert len(sol.log_registros) == qtd_logs_inicial
        assert sol.total_nao_lidas >= 1

    def test_avancar_estado_gera_log_e_notificacao(self):
        """Verifica que avançar estado popula tanto log quanto notificações."""
        cidadao = Cidadao("1", "Maria", "maria@email.com", "12345678901")
        sol = SolicitacaoDescarte("SOL-1", cidadao)

        logs_antes = len(sol.log_registros)
        notif_antes = sol.total_nao_lidas

        sol.avancar_estado()

        assert len(sol.log_registros) > logs_antes
        assert sol.total_nao_lidas > notif_antes

    def test_cancelar_gera_log_e_notificacao_alta_prioridade(self):
        """Verifica que cancelar gera log e notificação de alta prioridade."""
        cidadao = Cidadao("1", "Maria", "maria@email.com", "12345678901")
        sol = SolicitacaoDescarte("SOL-1", cidadao)

        sol.cancelar("Motivo teste")

        ultimo = sol.log_registros[-1]
        assert "cancelada" in ultimo["acao"].lower()

        notif_alta = [n for n in sol.notificacoes_pendentes if n["prioridade"] == "alta"]
        assert len(notif_alta) >= 1
