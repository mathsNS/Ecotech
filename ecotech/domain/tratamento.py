from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime
from .dispositivos import DispositivoEletronico

# Rastreamento de metodo aplicado - ABNER 24/02
# Relatorio de impacto por metodo - ABNER 24/02


class MetodoTratamento(ABC):
    # classe abstrata pra metodos de tratamento (padrao strategy)
    # permite trocar algoritmo de tratamento em tempo de execucao

    def __init__(self, custo_base_por_kg: float, reducao_impacto_percentual: float):
        self._custo_base_por_kg = custo_base_por_kg
        self._reducao_impacto_percentual = reducao_impacto_percentual

    @property
    def custo_base_por_kg(self) -> float:
        return self._custo_base_por_kg

    @property
    def reducao_impacto_percentual(self) -> float:
        return self._reducao_impacto_percentual

    @abstractmethod
    def obter_nome(self) -> str:
        pass

    @abstractmethod
    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        pass

    @abstractmethod
    def calcular_impacto_ambiental(
        self,
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        pass

    def __str__(self) -> str:
        return self.obter_nome()


class Reciclagem(MetodoTratamento):
    # metodo de reciclagem (desmonta e recupera os materiais que ainda tem utilidade) dai reduz impacto ambiental

    def __init__(self):
        super().__init__(custo_base_por_kg=15.0, reducao_impacto_percentual=80.0)

    def obter_nome(self) -> str:
        return "Reciclagem"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        # custo baseado no peso total * custo por kg
        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)

    def calcular_impacto_ambiental(
        self,
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        # calcula impacto reduzido pela reciclagem
        impacto_total = sum(d.calcular_impacto_ambiental()
                            for d in dispositivos)
        impacto_liquido = impacto_total * \
            (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)


class Reuso(MetodoTratamento):
    # metodo de reuso (recondiciona pra usar novamente)

    def __init__(self):
        super().__init__(custo_base_por_kg=8.0, reducao_impacto_percentual=95.0)

    def obter_nome(self) -> str:
        return "Reuso"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        # reuso é mais barato que reciclagem
        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)

    def calcular_impacto_ambiental(
        self,
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        # reuso reduz mais o impacto (95%)
        impacto_total = sum(d.calcular_impacto_ambiental()
                            for d in dispositivos)
        impacto_liquido = impacto_total * \
            (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)


class DescarteControlado(MetodoTratamento):
    # metodo de descarte controlado (vai pra um aterro especializado, diferente de um lixao etc)

    def __init__(self):
        super().__init__(custo_base_por_kg=25.0, reducao_impacto_percentual=40.0)

    def obter_nome(self) -> str:
        return "Descarte Controlado"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        # descarte controlado é mais caro que os outros
        peso_total = sum(d.peso_kg for d in dispositivos)
        return round(peso_total * self._custo_base_por_kg, 2)

    def calcular_impacto_ambiental(
        self,
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        # descarte controlado reduz menos o impacto (40%)
        impacto_total = sum(d.calcular_impacto_ambiental()
                            for d in dispositivos)
        impacto_liquido = impacto_total * \
            (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)


class RastreamentoMetodo:  # ABNER 24/02 - Rastreamento de metodo aplicado
    # ABNER 24/02 - rastreia quando e onde um metodo de tratamento foi aplicado
    # permite auditoria e analise historica de aplicacoes

    def __init__(self, id_aplicacao: str, metodo: MetodoTratamento, peso_total_kg: float):
        self._id_aplicacao = id_aplicacao  # ABNER 24/02
        self._metodo = metodo  # ABNER 24/02
        self._peso_total_kg = peso_total_kg  # ABNER 24/02
        self._data_aplicacao = datetime.now()  # ABNER 24/02
        self._custo = metodo.custo_base_por_kg * peso_total_kg  # ABNER 24/02
        self._impacto_evitado = (
            metodo.reducao_impacto_percentual / 100) * 100  # ABNER 24/02

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
        return round(self._custo, 2)

    @property
    def impacto_evitado(self) -> float:
        return round(self._impacto_evitado, 1)

    def obter_resumo(self) -> Dict:  # ABNER 24/02
        return {
            "id_aplicacao": self._id_aplicacao,
            "metodo": self._metodo.obter_nome(),
            "peso_kg": self._peso_total_kg,
            "data": self._data_aplicacao.isoformat(),
            "custo": self.custo,
            "impacto_evitado_percentual": self.impacto_evitado
        }

    def __str__(self) -> str:
        return f"Rastreamento {self._id_aplicacao}: {self._metodo.obter_nome()} ({self._peso_total_kg}kg)"


class RelatorioImpactoPorMetodo:  # ABNER 24/02 - Relatorio de impacto por metodo
    # ABNER 24/02 - consolida dados e gera relatorios de impacto por tipo de tratamento
    # permite analise comparativa entre diferentes metodos

    def __init__(self, titulo: str = "Relatorio de Impacto por Metodo"):
        self._titulo = titulo  # ABNER 24/02
        self._rastreamentos: List[RastreamentoMetodo] = []  # ABNER 24/02
        self._data_geracao = datetime.now()  # ABNER 24/02

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def data_geracao(self) -> datetime:
        return self._data_geracao

    def adicionar_rastreamento(self, rastreamento: RastreamentoMetodo):  # ABNER 24/02
        # ABNER 24/02 - adiciona um rastreamento ao relatorio
        self._rastreamentos.append(rastreamento)

    # ABNER 24/02
    def calcular_total_peso_por_metodo(self) -> Dict[str, float]:
        # ABNER 24/02 - calcula peso total processado por cada metodo
        totais = {}
        for rastr in self._rastreamentos:
            nome_metodo = rastr.metodo.obter_nome()
            if nome_metodo not in totais:
                totais[nome_metodo] = 0.0
            totais[nome_metodo] += rastr.peso_total_kg
        return {k: round(v, 2) for k, v in totais.items()}

    # ABNER 24/02
    def calcular_custo_total_por_metodo(self) -> Dict[str, float]:
        # ABNER 24/02 - calcula custo total por metodo
        totais = {}
        for rastr in self._rastreamentos:
            nome_metodo = rastr.metodo.obter_nome()
            if nome_metodo not in totais:
                totais[nome_metodo] = 0.0
            totais[nome_metodo] += rastr.custo
        return {k: round(v, 2) for k, v in totais.items()}

    # ABNER 24/02
    def calcular_impacto_evitado_por_metodo(self) -> Dict[str, float]:
        # ABNER 24/02 - calcula impacto ambiental evitado por cada metodo
        totais = {}
        for rastr in self._rastreamentos:
            nome_metodo = rastr.metodo.obter_nome()
            if nome_metodo not in totais:
                totais[nome_metodo] = 0.0
            # calcula quanto de impacto foi evitado
            impacto_evitado = (
                rastr.metodo.reducao_impacto_percentual / 100) * rastr.peso_total_kg
            totais[nome_metodo] += impacto_evitado
        return {k: round(v, 2) for k, v in totais.items()}

    def contar_aplicacoes_por_metodo(self) -> Dict[str, int]:  # ABNER 24/02
        # ABNER 24/02 - conta quantas vezes cada metodo foi aplicado
        contagens = {}
        for rastr in self._rastreamentos:
            nome_metodo = rastr.metodo.obter_nome()
            contagens[nome_metodo] = contagens.get(nome_metodo, 0) + 1
        return contagens

    def gerar_relatorio_completo(self) -> Dict:  # ABNER 24/02
        # ABNER 24/02 - gera relatorio consolidado com todas as metricas
        return {
            "titulo": self._titulo,
            "data_geracao": self._data_geracao.isoformat(),
            "total_rastreamentos": len(self._rastreamentos),
            "peso_por_metodo_kg": self.calcular_total_peso_por_metodo(),
            "custo_por_metodo": self.calcular_custo_total_por_metodo(),
            "impacto_evitado_por_metodo": self.calcular_impacto_evitado_por_metodo(),
            "aplicacoes_por_metodo": self.contar_aplicacoes_por_metodo()
        }

    def __str__(self) -> str:
        return f"Relatorio '{self._titulo}' com {len(self._rastreamentos)} rastreamentos"
