"""
Modulo de tratamento e rastreamento de dispositivos.

Implementa o padrão Strategy para métodos de tratamento ecológico e 
gerencia a auditoria e geração de relatórios de impacto.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Dict
from datetime import datetime
from .dispositivos import DispositivoEletronico

class MetodoTratamento(ABC):
    """
    Classe base para estratégias de tratamento ecológico.
    
    Utiliza o padrão Strategy permitindo trocar o algoritmo de tratamento em
    tempo de execução. Fornece atributos básicos de custo e redução de impacto.
    """

    def __init__(self, custo_base_por_kg: float, reducao_impacto_percentual: float):
        self._custo_base_por_kg = custo_base_por_kg
        self._reducao_impacto_percentual = reducao_impacto_percentual

    # -------------------
    # PROPERTIES
    # -------------------

    @property
    def custo_base_por_kg(self) -> float:
        return self._custo_base_por_kg

    @property
    def reducao_impacto_percentual(self) -> float:
        return self._reducao_impacto_percentual
    
    # ------------------
    # MÉTODOS ABSTRATOS
    # ------------------

    @abstractmethod
    def obter_nome(self) -> str:
        """Retorna o nome identificador do método."""
        pass

    @abstractmethod
    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        """Calcula custo total baseado no peso dos dispositivos."""
        pass

    @abstractmethod
    def calcular_impacto_ambiental(self, dispositivos: List[DispositivoEletronico]) -> float:
        """Calcula o impacto ambiental resultante do tratamento."""
        pass

    # ---------------
    # REPRESENTAÇÃO
    # ---------------

    def __str__(self) -> str:
        return self.obter_nome()

class Reciclagem(MetodoTratamento):
    """
    Método de tratamento que desmonta e recupera materiais reutilizáveis.

    A reciclagem reduz significativamente o impacto ambiental e possui custo
    intermediário.
    """

    def __init__(self):
        super().__init__(custo_base_por_kg = 15.0, reducao_impacto_percentual = 80.0)

    def obter_nome(self) -> str:
        return "Reciclagem"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)
    
    def calcular_impacto_ambiental(self, dispositivos: List[DispositivoEletronico]) -> float:
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)

class Reuso(MetodoTratamento):
    """
    Método que recondiciona dispositivos para reutilização.

    O reuso reduz quase totalmente o impacto ambiental e possui baixo custo.
    """

    def __init__(self):
        super().__init__(custo_base_por_kg = 8.0, reducao_impacto_percentual = 95.0)

    def obter_nome(self) -> str:
        return "Reuso"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)

    def calcular_impacto_ambiental(self, dispositivos: List[DispositivoEletronico]) -> float:
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)

class DescarteControlado(MetodoTratamento):
    """
    Método de descarte em aterro especializado.

    Custo elevado e redução de impacto moderada comparado aos demais métodos.
    """
    
    def __init__(self):
        super().__init__(custo_base_por_kg = 25.0, reducao_impacto_percentual = 40.0)

    def obter_nome(self) -> str:
        return "Descarte Controlado"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)
    
    def calcular_impacto_ambiental(self, dispositivos: List[DispositivoEletronico]) -> float:
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)

class RastreamentoMetodo:
    """
    Registra a aplicação de um método de tratamento.

    Armazena informações de quando, onde e com que peso o método foi usado,
    permitindo auditoria e análise histórica.
    """

    def __init__(self, id_aplicacao: str, metodo: MetodoTratamento, peso_total_kg: float):
        self._id_aplicacao = id_aplicacao
        self._metodo = metodo
        self._peso_total_kg = peso_total_kg
        self._data_aplicacao = datetime.now()

    # -------------------
    # PROPERTIES
    # -------------------

    @property
    def id_aplicacao(self) -> str:
        return self._id_aplicacao

    @property
    def metodo(self) -> MetodoTratamento:
        return self._metodo

    @property
    def peso_total_kg(self) -> float:
        return self._peso_total_kg

    @property
    def data_aplicacao(self) -> datetime:
        return self._data_aplicacao

    @property
    def custo(self) -> float:
        return round(self._metodo.custo_base_por_kg * self._peso_total_kg, 2)

    @property
    def impacto_evitado(self) -> float:
        return round((self._metodo.reducao_impacto_percentual / 100) * self._peso_total_kg, 2)

    def obter_resumo(self) -> Dict:
        return {
            "id_aplicacao": self._id_aplicacao,
            "metodo": self._metodo.obter_nome(),
            "peso_kg": self._peso_total_kg,
            "data": self._data_aplicacao.isoformat(),
            "custo": self.custo,
            "impacto_evitado_percentual": self.impacto_evitado
        }
    
    # ---------------
    # REPRESENTAÇÃO
    # ---------------
    
    def __str__(self) -> str:
        return f"Rastreamento {self._id_aplicacao}: {self._metodo.obter_nome()} ({self._peso_total_kg}kg)"

class RelatorioImpactoPorMetodo:
    """
    Consolida informações de rastreamentos para análise comparativa.

    Gera métricas de peso, custo e impacto evitado por método de tratamento.
    """
    def __init__(self, titulo: str = "Relatório de Impacto"):
        self._titulo = titulo
        self._rastreamentos: List[RastreamentoMetodo] = []
        self._data_geracao = datetime.now()

    # -------------------
    # PROPERTIES
    # -------------------
    
    @property
    def titulo(self) -> str:
        return self._titulo
    
    @property
    def rastreamentos(self) -> str:
        return self._rastreamentos
    
    @property
    def data_geracao(self) -> str:
        return self._data_geracao

    def adicionar_rastreamento(self, rastreamento: RastreamentoMetodo):
        self._rastreamentos.append(rastreamento)

    def gerar_relatorio_completo(self) -> Dict:
        """Calcula métricas agregadas por método de forma eficiente."""
        totais_peso = defaultdict(float)
        totais_custo = defaultdict(float)
        totais_impacto = defaultdict(float)
        contagens = defaultdict(int)

        for r in self._rastreamentos:
            nome = r.metodo.obter_nome()
            totais_peso[nome] += r.peso_total_kg
            totais_custo[nome] += r.custo
            totais_impacto[nome] += r.impacto_evitado
            contagens[nome] += 1

        return {
            "titulo": self._titulo,
            "data_geracao": self._data_geracao.isoformat(),
            "peso_por_metodo": dict(totais_peso),
            "custo_por_metodo": dict(totais_custo),
            "impacto_evitado_por_metodo": dict(totais_impacto),
            "aplicacoes_por_metodo": dict(contagens)
        }
    
    # ---------------
    # REPRESENTAÇÃO
    # ---------------
    
    def __str__(self) -> str:
        """Representação textual do relatório com número de rastreamentos."""
        return f"Relatorio '{self.titulo}' com {len(self._rastreamentos)} rastreamentos"