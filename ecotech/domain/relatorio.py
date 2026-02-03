# M- modulo de relatorios ambientais
# gera estatisticas sobre descarte, reciclagem e impacto ambiental
# calcula metricas de sustentabilidade do sistema

from typing import List, Dict
from datetime import datetime
from .descarte import SolicitacaoDescarte
from .estados import Reciclado, Reutilizado, Descartado

# M- em desenvolvimento - falta exportar para pdf (se der tempo e vcs quiserem, existe uma api que facilita isso)
# M- adicionar graficos de impacto (opcional tbm)

class RelatorioAmbiental:
    # M- classe para consolidar dados e gerar relatorios de impacto
    # agrupa solicitacoes e calcula metricas ambientais
    
    def __init__(self, titulo: str):
        self._titulo = titulo
        self._solicitacoes: List[SolicitacaoDescarte] = []  # lista de solicitacoes para analise
        self._data_geracao = datetime.now()  # timestamp de quando foi criado

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def data_geracao(self) -> datetime:
        return self._data_geracao

    def adicionar_solicitacao(self, solicitacao: SolicitacaoDescarte):
        self._solicitacoes.append(solicitacao)

    # M- calcula totais por tipo de tratamento final
    def calcular_total_peso_reciclado(self) -> float:
        # M- soma peso de todas as solicitacoes que foram recicladas
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
        # M- calcula quanto de impacto ambiental foi evitado pelos metodos de tratamento
        # cada metodo tem uma porcentagem de reducao de impacto
        impacto_total = 0.0
        
        for sol in self._solicitacoes:
            if sol.metodo_tratamento:
                impacto_original = sol.calcular_impacto_total()
                reducao = sol.metodo_tratamento.reducao_impacto_percentual
                impacto_evitado = impacto_original * (reducao / 100)
                impacto_total += impacto_evitado
                
        return round(impacto_total, 2)

    def gerar_relatorio(self) -> Dict:
        # M- retorna um dicionario com todas as metricas consolidadas
        # pode ser usado para exibir no sistema ou exportar para outros formatos
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
