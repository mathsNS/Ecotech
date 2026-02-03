from typing import List, Dict
from datetime import datetime
from .descarte import SolicitacaoDescarte
from .estados import Reciclado, Reutilizado, Descartado

# em desenvolvimento - falta exportar para pdf
# adicionar graficos de impacto

class RelatorioAmbiental:
    
    def __init__(self, titulo: str):
        self._titulo = titulo
        self._solicitacoes: List[SolicitacaoDescarte] = []
        self._data_geracao = datetime.now()

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def data_geracao(self) -> datetime:
        return self._data_geracao

    def adicionar_solicitacao(self, solicitacao: SolicitacaoDescarte):
        self._solicitacoes.append(solicitacao)

    def calcular_total_peso_reciclado(self) -> float:
        total = 0.0
        for sol in self._solicitacoes:
            if isinstance(sol.estado, Reciclado):
                total += sol.calcular_peso_total()
        return round(total, 2)

    def calcular_total_peso_reutilizado(self) -> float:
        total = 0.0
        for sol in self._solicitacoes:
            if isinstance(sol.estado, Reutilizado):
                total += sol.calcular_peso_total()
        return round(total, 2)

    def calcular_total_peso_descartado(self) -> float:
        total = 0.0
        for sol in self._solicitacoes:
            if isinstance(sol.estado, Descartado):
                total += sol.calcular_peso_total()
        return round(total, 2)

    def calcular_impacto_evitado(self) -> float:
        impacto_total = 0.0
        
        for sol in self._solicitacoes:
            if sol.metodo_tratamento:
                impacto_original = sol.calcular_impacto_total()
                reducao = sol.metodo_tratamento.reducao_impacto_percentual
                impacto_evitado = impacto_original * (reducao / 100)
                impacto_total += impacto_evitado
                
        return round(impacto_total, 2)

    def gerar_relatorio(self) -> Dict:
        return {
            "titulo": self._titulo,
            "data_geracao": self._data_geracao.isoformat(),
            "total_solicitacoes": len(self._solicitacoes),
            "peso_reciclado_kg": self.calcular_total_peso_reciclado(),
            "peso_reutilizado_kg": self.calcular_total_peso_reutilizado(),
            "peso_descartado_kg": self.calcular_total_peso_descartado(),
            "impacto_evitado": self.calcular_impacto_evitado()
        }

    def __str__(self) -> str:
        return f"Relatorio: {self._titulo} ({len(self._solicitacoes)} solicitacoes)"
