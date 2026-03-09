"""
Móodulo de relatórios ambientais

Gera estatísticas sobre descarte, reciclagem e impacto ambiental.
Calcula métricas de sustentabilidade do sistema.
"""

from typing import Dict
from datetime import datetime
from ..infrastructure.persistence.dados import Dados

# M- em desenvolvimento - falta exportar para pdf (se der tempo e vcs quiserem, existe uma api que facilita isso)
# M- adicionar graficos de impacto (opcional tbm)

class RelatorioAmbiental:
    def __init__(self, titulo: str, bd: Dados):
        self._titulo = titulo
        self.bd = bd
        self._data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def data_geracao(self) -> datetime:
        return self._data_geracao

    def total_solicitacoes(self) -> int:
        c = self.bd.conn.cursor()
        c.execute("""
        SELECT COUNT(*) as total
        FROM solicitacao_descarte
        """)
        resultado = c.fetchone()

        if not resultado:
            return 0
        else:
            return resultado['total']

    def calcular_peso_total_metodo(self, metodo: int) -> float:
        c = self.bd.conn.cursor()
        c.execute("""
        SELECT COALESCE(SUM(i.quantidade * d.peso_kg), 0.0) as peso_total
        FROM solicitacao_descarte s
        JOIN item_descarte i ON s.id = i.id_solicitacao
        JOIN dispositivo d ON i.id_dispositivo = d.id
        WHERE s.id_metodo_tratamento = ?
        """, (metodo, ))

        resultado = c.fetchone()

        return round(resultado['peso_total'], 2)

    def calcular_impacto_evitado(self) -> float:
        c = self.bd.conn.cursor()

        c.execute("""
        SELECT COALESCE(SUM(impacto_ambiental), 0.0) as impacto_ambiental_total
        FROM dispositivo
        """)

        row = c.fetchone()
        impacto_ambiental_total = row['impacto_ambiental_total']

        c.execute("""
        SELECT COALESCE(SUM(? * (1.0- m.reducao_impacto_percentual / 100.0)), 0.0) as impacto_evitado
        FROM solicitacao_descarte s
        JOIN item_descarte i ON s.id = i.id_solicitacao
        JOIN dispositivo d ON i.id_dispositivo = d.id
        JOIN metodo_tratamento m ON s.id_metodo_tratamento = m.id
        """, (impacto_ambiental_total, ))

        resultado = c.fetchone()

        return round(resultado['impacto_evitado'], 2)

    def gerar_relatorio(self) -> Dict:
        return {
            "titulo": self._titulo,
            "data_geracao": self._data_geracao,
            "total_solicitacoes": self.total_solicitacoes(),
            "peso_reciclado_kg": self.calcular_peso_total_metodo(1),
            "peso_reutilizado_kg": self.calcular_peso_total_metodo(2),
            "peso_descartado_kg": self.calcular_peso_total_metodo(3),
            "impacto_evitado": self.calcular_impacto_evitado()
        }
    
    def __str__(self) -> str:
        return f"Relatorio: {self._titulo} ({self.total_solicitacoes()} solicitações)"