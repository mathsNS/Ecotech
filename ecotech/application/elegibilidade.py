"""Seleção explicável de bases aptas a uma coleta domiciliar."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Tuple

from .geolocalizacao import CalculadorDistancia, DistanciaHaversine
from ..domain.logistica import BaseOperacional, Coordenadas


@dataclass(frozen=True)
class DemandaColeta:
    coordenadas: Coordenadas
    categorias: frozenset[str]
    peso_kg: float
    agendada_para: datetime

    def __post_init__(self):
        object.__setattr__(
            self, 'categorias',
            frozenset(c.strip().lower() for c in self.categorias if c.strip()),
        )
        if not self.categorias:
            raise ValueError("a coleta deve possuir ao menos uma categoria")
        if self.peso_kg <= 0:
            raise ValueError("peso da coleta deve ser positivo")


@dataclass(frozen=True)
class BaseElegivel:
    base: BaseOperacional
    distancia_km: float


@dataclass(frozen=True)
class AvaliacaoElegibilidade:
    base_id: str
    elegivel: bool
    motivos: Tuple[str, ...]
    distancia_km: float


class ServicoElegibilidade:
    def __init__(self, distancia: CalculadorDistancia | None = None):
        self._distancia = distancia or DistanciaHaversine()

    def avaliar(
        self, base: BaseOperacional, demanda: DemandaColeta,
        agora: datetime | None = None,
    ) -> AvaliacaoElegibilidade:
        agora = agora or datetime.now()
        distancia = self._distancia.calcular_km(base.coordenadas, demanda.coordenadas)
        motivos = []
        if not base.empresa_ativa:
            motivos.append('empresa_inativa')
        if not base.ativa:
            motivos.append('base_inativa')
        if not base.realiza_coleta_domiciliar:
            motivos.append('sem_coleta_domiciliar')
        if '*' not in base.categorias_atendidas and not demanda.categorias.issubset(
            base.categorias_atendidas
        ):
            motivos.append('categoria_nao_atendida')
        if base.capacidade_disponivel_kg < demanda.peso_kg:
            motivos.append('capacidade_insuficiente')
        if base.disponibilidade and not any(
            janela.contem(demanda.agendada_para) for janela in base.disponibilidade
        ):
            motivos.append('fora_da_janela')
        if distancia > base.raio_atendimento_km:
            motivos.append('fora_do_raio')
        if base.indisponivel_ate and base.indisponivel_ate > agora:
            motivos.append('temporariamente_indisponivel')
        return AvaliacaoElegibilidade(
            base.id, not motivos, tuple(motivos), distancia
        )

    def selecionar(
        self, bases: Iterable[BaseOperacional], demanda: DemandaColeta,
        agora: datetime | None = None,
    ) -> list[BaseElegivel]:
        resultado = []
        for base in bases:
            avaliacao = self.avaliar(base, demanda, agora)
            if avaliacao.elegivel:
                resultado.append(BaseElegivel(base, avaliacao.distancia_km))
        return resultado
