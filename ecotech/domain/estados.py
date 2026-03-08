"""
Módulo de estados para o ciclo de vida de uma solicitação de descarte.

Implementa o padrão State para controlar transições válidas.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from datetime import datetime
from typing import List

if TYPE_CHECKING:
    from .descarte import SolicitacaoDescarte

class EstadoDescarte(ABC):
    """Classe base abstrata para estados da solicitacao."""
    
    def __init__(self):
        self._data_entrada = datetime.now()
        self._log_transicoes: List[str] = []

    @property
    def data_entrada(self) -> datetime:
        return self._data_entrada
    
    @property
    def log_transicoes(self) -> List[str]:
        """Retorna todas as notificações."""
        return self._log_transicoes.copy()
        
    @abstractmethod
    def obter_nome(self) -> str:
        """Retorna o nome do estado atual."""
        pass

    def pode_avancar(self) -> bool:
        """Verifica se a transição para o próximo estado é permitida."""
        return False

    def pode_cancelar(self) -> bool:
        """Verifica se o cancelamento é permitido neste estado."""
        return False

    def avancar(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        """Executa a transição de estado com validação."""
        if not self.pode_avancar():
            raise ValueError(f"Não é possível avançar a partir do estado {self.obter_nome()}")
        
        novo_estado = self._proximo_estado(solicitacao)
        self.adicionar_log(f"[LOG] Transição: {self.obter_nome()} -> {novo_estado.obter_nome()}")
        
        return novo_estado

    def adicionar_log(self, mensagem: str) -> None:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        log_transicao = f"[{timestamp}] {mensagem}"

        self._log_transicoes.append(log_transicao)

    @abstractmethod
    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        """Define a lógica de transição para a subclasse."""
        pass

    def __str__(self) -> str:
        return self.obter_nome()

class Solicitado(EstadoDescarte):

    def obter_nome(self) -> str:
        return "Solicitado"

    def pode_avancar(self) -> bool:
        return True

    def pode_cancelar(self) -> bool:
        return True

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        return Coletado()

class Coletado(EstadoDescarte):

    def obter_nome(self) -> str:
        return "Coletado"

    def pode_avancar(self) -> bool:
        return True

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        return EmProcessamento()

class EmProcessamento(EstadoDescarte):

    def obter_nome(self) -> str:
        return "Em Processamento"

    def pode_avancar(self) -> bool:
        return True

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        metodo = solicitacao.metodo_tratamento
        nome = metodo.obter_nome().lower()
        if "recicla" in nome:
            return Reciclado()
        elif "reuso" in nome:
            return Reutilizado()
        else:
            return Descartado()
            
class EstadoFinal(EstadoDescarte, ABC):
    """Classe base para estados que finalizam o fluxo."""
    def pode_avancar(self) -> bool:
        return False

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        raise ValueError("Estado final não permite transição.")

class Reciclado(EstadoFinal):
    def obter_nome(self) -> str:
        return "Reciclado"

class Reutilizado(EstadoFinal):
    def obter_nome(self) -> str:
        return "Reutilizado"

class Descartado(EstadoFinal):
    def obter_nome(self) -> str:
        return "Descartado"

class Cancelado(EstadoFinal):
    def __init__(self, motivo: str = ""):
        super().__init__()
        self._motivo = motivo

    @property
    def motivo(self) -> str:
        return self._motivo

    def obter_nome(self) -> str:
        return "Cancelado"