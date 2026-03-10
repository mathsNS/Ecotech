"""
Módulo de Mixins reutilizáveis.

Fornece comportamentos transversais que podem ser compostos em classes
de domínio via herança múltipla, sem criar acoplamento entre hierarquias.
"""

from datetime import datetime
from typing import List, Dict


class LoggableMixin:
    """
    Mixin que adiciona capacidade de logging/auditoria a qualquer classe.

    Registra ações com timestamp, permitindo rastreabilidade e auditoria
    de operações realizadas sobre o objeto.

    Atributos:
        _log_registros: Lista interna com todas as entradas de log.
    """

    def __init_log__(self) -> None:
        """Inicializa a estrutura interna de log."""
        self._log_registros: List[Dict[str, str]] = []

    def registrar_log(self, acao: str, detalhe: str = "") -> None:
        """
        Registra uma entrada de log com timestamp.

        Args:
            acao: Descrição curta da ação realizada.
            detalhe: Informação adicional sobre a ação.
        """
        entrada = {
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "acao": acao,
            "detalhe": detalhe,
        }
        self._log_registros.append(entrada)

    @property
    def log_registros(self) -> List[Dict[str, str]]:
        """Retorna cópia defensiva dos registros de log."""
        return self._log_registros.copy()

    @property
    def ultimo_log(self) -> Dict[str, str]:
        """Retorna a última entrada de log, ou dicionário vazio se não houver."""
        if self._log_registros:
            return self._log_registros[-1].copy()
        return {}

    def limpar_log(self) -> None:
        """Remove todas as entradas de log."""
        self._log_registros.clear()


class NotificavelMixin:
    """
    Mixin que adiciona sistema de notificações a qualquer classe.

    Permite que objetos emitam e armazenem notificações para consumo
    posterior, com controle de leitura e prioridade.

    Atributos:
        _fila_notificacoes: Lista interna de notificações pendentes.
    """

    def __init_notificacoes__(self) -> None:
        """Inicializa a fila interna de notificações."""
        self._fila_notificacoes: List[Dict] = []

    def emitir_notificacao(self, titulo: str, mensagem: str, prioridade: str = "normal") -> None:
        """
        Emite uma nova notificação.

        Args:
            titulo: Título da notificação.
            mensagem: Corpo da notificação.
            prioridade: Nível de prioridade ('baixa', 'normal', 'alta').

        Raises:
            ValueError: Se a prioridade não for válida.
        """
        prioridades_validas = ("baixa", "normal", "alta")
        if prioridade not in prioridades_validas:
            raise ValueError(f"Prioridade deve ser uma de: {prioridades_validas}")

        notificacao = {
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "titulo": titulo,
            "mensagem": mensagem,
            "prioridade": prioridade,
            "lida": False,
        }
        self._fila_notificacoes.append(notificacao)

    @property
    def notificacoes_pendentes(self) -> List[Dict]:
        """Retorna notificações ainda não lidas."""
        return [n for n in self._fila_notificacoes if not n["lida"]]

    @property
    def total_nao_lidas(self) -> int:
        """Retorna a quantidade de notificações não lidas."""
        return len(self.notificacoes_pendentes)

    def marcar_como_lida(self, indice: int) -> None:
        """
        Marca uma notificação como lida pelo índice.

        Args:
            indice: Posição da notificação na fila.

        Raises:
            IndexError: Se o índice estiver fora do intervalo.
        """
        if indice < 0 or indice >= len(self._fila_notificacoes):
            raise IndexError("Índice de notificação fora do intervalo.")
        self._fila_notificacoes[indice]["lida"] = True

    def marcar_todas_como_lidas(self) -> None:
        """Marca todas as notificações como lidas."""
        for notificacao in self._fila_notificacoes:
            notificacao["lida"] = True

    def limpar_notificacoes_lidas(self) -> None:
        """Remove todas as notificações já lidas."""
        self._fila_notificacoes = [n for n in self._fila_notificacoes if not n["lida"]]
