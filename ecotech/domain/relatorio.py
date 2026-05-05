"""Módulo de relatórios ambientais.

Gera estatísticas sobre descarte, reciclagem e impacto ambiental,
calculando métricas de sustentabilidade do sistema.
"""

from typing import List, Dict
from datetime import datetime
from .descarte import SolicitacaoDescarte
from .estados import Reciclado, Reutilizado, Descartado


class RelatorioAmbiental:
    """Consolida dados de solicitações e gera relatórios de impacto ambiental.

    Agrupa solicitações de descarte e calcula métricas ambientais
    como peso reciclado, reutilizado e impacto evitado.
    """
    
    def __init__(self, titulo: str):
        """Inicializa o relatório com título e timestamp."""
        self._titulo = titulo
        self._solicitacoes: List[SolicitacaoDescarte] = []
        self._data_geracao = datetime.now()

    @property
    def titulo(self) -> str:
        """Retorna o título do relatório."""
        return self._titulo

    @property
    def data_geracao(self) -> datetime:
        """Retorna a data de geração do relatório."""
        return self._data_geracao

    def adicionar_solicitacao(self, solicitacao: SolicitacaoDescarte):
        """Adiciona uma solicitação ao relatório para análise."""
        self._solicitacoes.append(solicitacao)

    def calcular_total_peso_reciclado(self) -> float:
        """Soma o peso de todas as solicitações recicladas."""
        total = 0.0
        for sol in self._solicitacoes:
            if isinstance(sol.estado, Reciclado):
                total += sol.calcular_peso_total()
        return round(total, 2)

    def calcular_total_peso_reutilizado(self) -> float:
        """Soma o peso de todas as solicitações reutilizadas."""
        total = 0.0
        for sol in self._solicitacoes:
            if isinstance(sol.estado, Reutilizado):
                total += sol.calcular_peso_total()
        return round(total, 2)

    def calcular_total_peso_descartado(self) -> float:
        """Soma o peso de todas as solicitações descartadas."""
        total = 0.0
        for sol in self._solicitacoes:
            if isinstance(sol.estado, Descartado):
                total += sol.calcular_peso_total()
        return round(total, 2)

    def calcular_impacto_evitado(self) -> float:
        """Soma o impacto evitado de todas as solicitações."""
        impacto_total = 0.0
        for sol in self._solicitacoes:
            impacto_total += sol.impacto_evitado_db
        return round(impacto_total, 2)

    def calcular_eficiencia_reciclagem(self) -> float:
        """Percentual do peso reciclado/reutilizado sobre o total processado."""
        total = sum(
            sol.calcular_peso_total() for sol in self._solicitacoes
            if isinstance(sol.estado, (Reciclado, Reutilizado, Descartado))
        )
        if total == 0:
            return 0.0
        tratado = self.calcular_total_peso_reciclado() + self.calcular_total_peso_reutilizado()
        return round((tratado / total) * 100, 2)

    def gerar_relatorio(self) -> Dict:
        """Retorna dicionário com todas as métricas consolidadas."""
        return {
            "titulo": self._titulo,
            "data_geracao": self._data_geracao.isoformat(),
            "total_solicitacoes": len(self._solicitacoes),
            "peso_reciclado_kg": self.calcular_total_peso_reciclado(),
            "peso_reutilizado_kg": self.calcular_total_peso_reutilizado(),
            "peso_descartado_kg": self.calcular_total_peso_descartado(),
            "impacto_evitado": self.calcular_impacto_evitado(),
            "eficiencia_reciclagem_pct": self.calcular_eficiencia_reciclagem()
        }

    def __str__(self) -> str:
        """Representação textual do relatório."""
        return f"Relatorio: {self._titulo} ({len(self._solicitacoes)} solicitacoes)"
