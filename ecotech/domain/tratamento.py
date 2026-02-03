from abc import ABC, abstractmethod
from typing import List
from .dispositivos import DispositivoEletronico

# TODO: adicionar rastreamento de metodo aplicado
# TODO: criar relatorio de impacto por metodo

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
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
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
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
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
        impacto_total = sum(d.calcular_impacto_ambiental() for d in dispositivos)
        impacto_liquido = impacto_total * (1 - self._reducao_impacto_percentual / 100)
        return round(impacto_liquido, 2)
