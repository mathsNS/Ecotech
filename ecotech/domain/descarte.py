# modulo central de descarte
# contem as classes principais para gerenciar solicitacoes de descarte
# usa composicao para relacionar usuarios, dispositivos e pontos de coleta

from datetime import datetime
from typing import List, Optional, Dict
from .dispositivos import DispositivoEletronico
from .usuarios import Usuario
from .estados import EstadoDescarte, Solicitado, Cancelado
from .tratamento import MetodoTratamento

# precisa implementar validacoes de ponto de coleta
# adicionar rastreamento de entrega

class ItemDescarte:
    # A- representa um item individual de descarte (composicao com DispositivoEletronico)
    # um item e um dispositivo + quantidade + observacoes
    
    def __init__(
        self,
        dispositivo: DispositivoEletronico,
        quantidade: int = 1,
        observacoes: str = ""
    ):
        if quantidade <= 0:
            raise ValueError("quantidade deve ser positiva")
            
        self._dispositivo = dispositivo
        self._quantidade = quantidade
        self._observacoes = observacoes

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
        # A- peso total = peso unitario * quantidade
        return self._dispositivo.peso_kg * self._quantidade

    def calcular_impacto_total(self) -> float:
        # A- impacto total = impacto unitario * quantidade
        return self._dispositivo.calcular_impacto_ambiental() * self._quantidade

    def __str__(self) -> str:
        return f"{self._quantidade}x {self._dispositivo.nome}"


class PontoColeta:
    # M- representa um ponto de coleta fisico
    # tem capacidade limitada e pode ser ativado/desativado
    
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
        self._latitude = latitude  # coordenadas para localizacao no mapa
        self._longitude = longitude
        self._ativo = True
        self._capacidade_kg = capacidade_kg  # capacidade maxima em kg
        self._ocupacao_atual_kg = 0.0  # quanto ja esta ocupado

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

    def pode_receber(self, peso_kg: float) -> bool:
        # M- verifica se ponto tem espaco disponivel para receber o peso
        return self._ativo and (self._ocupacao_atual_kg + peso_kg) <= self._capacidade_kg

    def adicionar_ocupacao(self, peso_kg: float):
        if not self.pode_receber(peso_kg):
            raise ValueError("ponto de coleta sem capacidade")
        self._ocupacao_atual_kg += peso_kg
    
    def calcular_disponibilidade_percentual(self) -> float:
        if self._capacidade_kg == 0:
            return 0.0
        ocupacao_percentual = (self._ocupacao_atual_kg / self._capacidade_kg) * 100
        return round(100 - ocupacao_percentual, 1)

    def __str__(self) -> str:
        return f"{self._nome} - {self._endereco}"


class SolicitacaoDescarte:
    # classe central que representa uma solicitacao de descarte
    # agrega varios itens, tem um estado, ponto de coleta e metodo de tratamento
    # M- usa padrao State para gerenciar ciclo de vida da solicitacao
    
    def __init__(
        self,
        id: str,
        usuario: Usuario,
        ponto_coleta: Optional[PontoColeta] = None
    ):
        self._id = id
        self._usuario = usuario  # M- quem fez a solicitacao
        self._ponto_coleta = ponto_coleta  # M- onde sera entregue
        self._itens: List[ItemDescarte] = []  # A- lista de itens a descartar
        self._estado: EstadoDescarte = Solicitado()  # estado inicial
        self._metodo_tratamento: Optional[MetodoTratamento] = None  # definido depois
        self._data_criacao = datetime.now()
        self._data_agendamento: Optional[datetime] = None  # quando sera coletado

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

    @property
    def data_criacao(self) -> datetime:
        return self._data_criacao

    @property
    def data_agendamento(self) -> Optional[datetime]:
        return self._data_agendamento

    @data_agendamento.setter
    def data_agendamento(self, valor: datetime):
        self._data_agendamento = valor

    def adicionar_item(self, item: ItemDescarte):
        # A- adiciona um dispositivo a solicitacao
        self._itens.append(item)

    def remover_item(self, item: ItemDescarte):
        if item in self._itens:
            self._itens.remove(item)

    def calcular_peso_total(self) -> float:
        # A- soma o peso de todos os itens
        return sum(item.calcular_peso_total() for item in self._itens)

    def calcular_impacto_total(self) -> float:
        # A- soma o impacto ambiental de todos os itens
        return sum(item.calcular_impacto_total() for item in self._itens)

    def avancar_estado(self):
        # usa o padrao State para transicionar entre estados
        self._estado = self._estado.avancar(self)

    def cancelar(self, motivo: str = ""):
        if not self._estado.pode_cancelar():
            raise ValueError("nao e possivel cancelar neste estado")
        self._estado = Cancelado(motivo)

    def obter_resumo(self) -> Dict:
        return {
            "id": self._id,
            "usuario": self._usuario.nome,
            "estado": self._estado.obter_nome(),
            "total_itens": len(self._itens),
            "peso_total_kg": self.calcular_peso_total(),
            "impacto_total": self.calcular_impacto_total(),
            "data_criacao": self._data_criacao.isoformat()
        }

    def __str__(self) -> str:
        return f"Solicitacao {self._id} - {self._estado.obter_nome()}"
