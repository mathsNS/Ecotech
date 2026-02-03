from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .descarte import SolicitacaoDescarte

# TODO: adicionar log de transicoes de estado
# TODO: implementar notificacao ao usuario em cada mudanca

class EstadoDescarte(ABC):
    
    def __init__(self):
        self._data_entrada = datetime.now()

    @property
    def data_entrada(self) -> datetime:
        return self._data_entrada

    @abstractmethod
    def obter_nome(self) -> str:
        pass

    @abstractmethod
    def pode_avancar(self) -> bool:
        pass

    @abstractmethod
    def pode_cancelar(self) -> bool:
        pass

    def avancar(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        if not self.pode_avancar():
            raise ValueError(
                f"nao e possivel avancar do estado {self.obter_nome()}"
            )
        return self._proximo_estado(solicitacao)

    @abstractmethod
    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
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

    def pode_cancelar(self) -> bool:
        return False

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        return EmProcessamento()


class EmProcessamento(EstadoDescarte):
    
    def obter_nome(self) -> str:
        return "Em Processamento"

    def pode_avancar(self) -> bool:
        return True

    def pode_cancelar(self) -> bool:
        return False

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        if solicitacao.metodo_tratamento:
            nome_metodo = solicitacao.metodo_tratamento.obter_nome()
            if "Recicla" in nome_metodo:
                return Reciclado()
            elif "Reuso" in nome_metodo:
                return Reutilizado()
            else:
                return Descartado()
        return Descartado()


class Reciclado(EstadoDescarte):
    
    def obter_nome(self) -> str:
        return "Reciclado"

    def pode_avancar(self) -> bool:
        return False

    def pode_cancelar(self) -> bool:
        return False

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        raise ValueError("estado final nao pode avancar")


class Reutilizado(EstadoDescarte):
    
    def obter_nome(self) -> str:
        return "Reutilizado"

    def pode_avancar(self) -> bool:
        return False

    def pode_cancelar(self) -> bool:
        return False

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        raise ValueError("estado final nao pode avancar")


class Descartado(EstadoDescarte):
    
    def obter_nome(self) -> str:
        return "Descartado"

    def pode_avancar(self) -> bool:
        return False

    def pode_cancelar(self) -> bool:
        return False

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        raise ValueError("estado final nao pode avancar")


class Cancelado(EstadoDescarte):
    
    def __init__(self, motivo: str = ""):
        super().__init__()
        self._motivo = motivo

    @property
    def motivo(self) -> str:
        return self._motivo

    def obter_nome(self) -> str:
        return "Cancelado"

    def pode_avancar(self) -> bool:
        return False

    def pode_cancelar(self) -> bool:
        return False

    def _proximo_estado(self, solicitacao: 'SolicitacaoDescarte') -> 'EstadoDescarte':
        raise ValueError("estado cancelado nao pode avancar")
