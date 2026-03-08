"""
Módulo central de descarte.
Contem as classes principais para gerenciar solicitacoes de descarte.
Usa composicao para relacionar usuarios, dispositivos e pontos de coleta.
"""

from datetime import datetime
from typing import List, Optional, Dict
from .dispositivos import DispositivoEletronico
from .usuarios import Usuario
from .estados import EstadoDescarte, Solicitado, Cancelado
from .tratamento import MetodoTratamento

class RastreamentoEntrega:
    """Registra o status e histórico de movimentação de uma solicitação."""
    def __init__(self, id_rastreio: str):
        self.id_rastreio = id_rastreio
        self.historico: List[str] = ["Solicitação iniciada"]

    def atualizar_status(self, mensagem: str):
        self.historico.append(f"{datetime.now()}: {mensagem}")


class ItemDescarte:
    """Representa um item individual de descarte."""
    
    def __init__(
        self,
        dispositivo: DispositivoEletronico,
        quantidade: int = 1,
        observacoes: str = ""
    ):
        """Inicializa um item de descarte."""
        if quantidade <= 0:
            raise ValueError("quantidade deve ser positiva")
            
        self._dispositivo = dispositivo
        self._quantidade = quantidade
        self._observacoes = observacoes

    # -------------------
    # PROPERTIES
    # -------------------

    @property
    def dispositivo(self) -> DispositivoEletronico:
        return self._dispositivo

    @property
    def quantidade(self) -> int:
        return self._quantidade

    @quantidade.setter
    def quantidade(self, valor: int):
        if valor <= 0:
            raise ValueError("quantidade deve ser positiva")
        self._quantidade = valor

    @property
    def observacoes(self) -> str:
        return self._observacoes

    def calcular_peso_total(self) -> float:
        """Retorna peso total (peso unitário * quantidade)."""
        return self._dispositivo.peso_kg * self._quantidade

    def calcular_impacto_total(self) -> float:
        """Retorna impacto total (impacto unitário * quantidade)."""
        return self._dispositivo.calcular_impacto_ambiental() * self._quantidade

    # ---------------
    # REPRESENTAÇÃO
    # ---------------
    
    def __str__(self) -> str:
        return f"{self._quantidade}x {self._dispositivo.nome}"


class PontoColeta:
    """Representa um ponto de coleta fisico com capacidade controlada."""
    
    def __init__(
        self,
        id: str,
        nome: str,
        endereco: str,
        latitude: float,
        longitude: float,
        capacidade_kg: float = 1000.0
    ):
        self._id = id
        self._nome = nome
        self._endereco = endereco
        self._latitude = latitude
        self._longitude = longitude
        self._ativo = True
        self._capacidade_kg = capacidade_kg
        self._ocupacao_atual_kg = 0.0

    # -------------------
    # PROPERTIES
    # -------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def endereco(self) -> str:
        return self._endereco

    @property
    def ativo(self) -> bool:
        return self._ativo

    @property
    def capacidade_kg(self) -> float:
        return self._capacidade_kg

    @property
    def ocupacao_atual_kg(self) -> float:
        return self._ocupacao_atual_kg

    def validar_e_receber(self, peso_kg: float):
        """Valida se o ponto pode receber e incrementa a ocupação."""
        if not self.pode_receber(peso_kg):
            raise ValueError("Ponto de coleta excederia a capacidade máxima.")
        self.adicionar_ocupacao(peso_kg)

    def pode_receber(self, peso_kg: float) -> bool:
        """Verifica capacidade disponível e status ativo."""
        return self._ativo and (self._ocupacao_atual_kg + peso_kg) <= self._capacidade_kg

    def adicionar_ocupacao(self, peso_kg: float):
        self._ocupacao_atual_kg += peso_kg
    
    def calcular_disponibilidade_percentual(self) -> float:
        if self._capacidade_kg == 0:
            return 0.0
        ocupacao_percentual = (self._ocupacao_atual_kg / self._capacidade_kg) * 100
        return round(100 - ocupacao_percentual, 1)

    # ---------------
    # REPRESENTAÇÃO
    # ---------------
    
    def __str__(self) -> str:
        return f"{self._nome} - {self._endereco}"


class SolicitacaoDescarte:
    """Classe central que gerencia o ciclo de vida da solicitação de descarte."""
    
    def __init__(
        self,
        id: str,
        usuario: Usuario,
        ponto_coleta: Optional[PontoColeta] = None
    ):
        self._id = id
        self._usuario = usuario
        self._ponto_coleta = ponto_coleta
        self._itens: List[ItemDescarte] = []
        self._estado: EstadoDescarte = Solicitado()
        self._metodo_tratamento: Optional[MetodoTratamento] = None
        self._data_criacao = datetime.now()
        self._data_agendamento: Optional[datetime] = None
        self.rastreamento = RastreamentoEntrega(f"R-{id}")

    # -------------------
    # PROPERTIES
    # -------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def usuario(self) -> Usuario:
        return self._usuario

    @property
    def ponto_coleta(self) -> Optional[PontoColeta]:
        return self._ponto_coleta

    @ponto_coleta.setter
    def ponto_coleta(self, valor: PontoColeta):
        self._ponto_coleta = valor

    @property
    def itens(self) -> List[ItemDescarte]:
        return self._itens.copy()

    @property
    def estado(self) -> EstadoDescarte:
        return self._estado

    @property
    def metodo_tratamento(self) -> Optional[MetodoTratamento]:
        return self._metodo_tratamento

    @metodo_tratamento.setter
    def metodo_tratamento(self, valor: MetodoTratamento):
        self._metodo_tratamento = valor

    def adicionar_item(self, item: ItemDescarte):
        self._itens.append(item)

    def remover_item(self, item: ItemDescarte):
        if item in self._itens:
            self._itens.remove(item)

    def calcular_peso_total(self) -> float:
        return sum(item.calcular_peso_total() for item in self._itens)

    def calcular_impacto_total(self) -> float:
        return sum(item.calcular_impacto_total() for item in self._itens)

    def avancar_estado(self):
        """Transiciona para o próximo estado e registra no rastreamento."""
        self._estado = self._estado.avancar(self)
        self.rastreamento.atualizar_status(f"Estado mudado para {self._estado.obter_nome()}")

    def cancelar(self, motivo: str = ""):
        if not self._estado.pode_cancelar():
            raise ValueError("Não é possível cancelar neste estado")
        self._estado = Cancelado(motivo)
        self.rastreamento.atualizar_status(f"Cancelado: {motivo}")

    def obter_resumo(self) -> Dict:
        return {
            "id": self._id,
            "usuario": self._usuario.nome,
            "estado": self._estado.obter_nome(),
            "peso_total_kg": self.calcular_peso_total(),
            "data_criacao": self._data_criacao.isoformat()
        }
    
    # ---------------
    # REPRESENTAÇÃO
    # ---------------

    def __str__(self) -> str:
        return f"Solicitação {self._id} - {self._estado.obter_nome()}"