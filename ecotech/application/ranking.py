"""Ranking determinístico e auditável das bases elegíveis."""

from dataclasses import asdict, dataclass
from typing import Iterable

from .elegibilidade import BaseElegivel


@dataclass(frozen=True)
class PesosRanking:
    distancia: float = 0.60
    disponibilidade: float = 0.15
    capacidade: float = 0.15
    carga: float = 0.10

    def __post_init__(self):
        valores = asdict(self).values()
        if any(valor < 0 for valor in valores) or sum(valores) <= 0:
            raise ValueError("pesos do ranking devem ser não negativos e possuir soma positiva")


@dataclass(frozen=True)
class ResultadoRanking:
    posicao: int
    base_id: str
    score: float
    snapshot: dict


class ServicoRanking:
    def __init__(self, pesos: PesosRanking | None = None):
        self._pesos = pesos or PesosRanking()

    def ordenar(self, candidatas: Iterable[BaseElegivel]) -> list[ResultadoRanking]:
        candidatas = list(candidatas)
        if not candidatas:
            return []
        calculados = []
        for candidata in candidatas:
            base = candidata.base
            fator_distancia = 1 - min(
                candidata.distancia_km / base.raio_atendimento_km, 1
            )
            fator_capacidade = min(
                base.capacidade_disponivel_kg / base.capacidade_kg, 1
            )
            fator_carga = 1 / (1 + base.carga_operacional)
            fator_disponibilidade = 0.0 if base.indisponivel_ate else 1.0
            fatores = {
                'distancia': round(fator_distancia, 6),
                'disponibilidade': round(fator_disponibilidade, 6),
                'capacidade': round(fator_capacidade, 6),
                'carga': round(fator_carga, 6),
            }
            score = sum(
                fatores[nome] * peso for nome, peso in asdict(self._pesos).items()
            ) / sum(asdict(self._pesos).values())
            snapshot = {
                'distancia_km': candidata.distancia_km,
                'capacidade_disponivel_kg': base.capacidade_disponivel_kg,
                'carga_operacional': base.carga_operacional,
                'fatores': fatores,
                'pesos': asdict(self._pesos),
            }
            calculados.append((round(score, 8), base.id, snapshot))
        calculados.sort(key=lambda item: (-item[0], item[1]))
        return [
            ResultadoRanking(i, base_id, score, snapshot)
            for i, (score, base_id, snapshot) in enumerate(calculados, 1)
        ]
