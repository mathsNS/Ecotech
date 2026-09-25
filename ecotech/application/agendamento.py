"""Negociação consensual da janela de coleta."""

from datetime import datetime, timedelta, timezone


class ServicoAgendamento:
    def __init__(self, dados):
        self._dados = dados

    @staticmethod
    def validar(inicio, fim, agora=None):
        agora = agora or datetime.now(timezone(timedelta(hours=-3)))
        if inicio >= fim:
            raise ValueError("início deve anteceder o fim")
        if inicio < agora:
            raise ValueError("janela não pode estar no passado")
        if (fim - inicio).total_seconds() > 24 * 3600:
            raise ValueError("janela não pode exceder 24 horas")

    def solicitar(self, solicitacao_id, cidadao_id, inicio, fim, agora=None):
        agora = agora or datetime.now(timezone(timedelta(hours=-3)))
        self.validar(inicio, fim, agora)
        return self._dados.registrar_janela_agendamento(
            solicitacao_id,
            cidadao_id,
            inicio.isoformat(),
            fim.isoformat(),
            agora.isoformat(),
        )

    def propor(self, solicitacao_id, usuario_id, inicio, fim, agora=None):
        agora = agora or datetime.now(timezone(timedelta(hours=-3)))
        self.validar(inicio, fim, agora)
        return self._dados.propor_agendamento(
            solicitacao_id,
            usuario_id,
            inicio.isoformat(),
            fim.isoformat(),
            agora.isoformat(),
        )

    def aceitar(self, solicitacao_id, usuario_id, agora=None):
        agora = agora or datetime.now(timezone(timedelta(hours=-3)))
        return self._dados.aceitar_agendamento(solicitacao_id, usuario_id, agora.isoformat())

    def rejeitar(self, solicitacao_id, usuario_id, agora=None):
        agora = agora or datetime.now(timezone(timedelta(hours=-3)))
        return self._dados.rejeitar_agendamento(solicitacao_id, usuario_id, agora.isoformat())
