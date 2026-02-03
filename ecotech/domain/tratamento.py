from abc import ABC, abstractmethod
from typing import List
from .dispositivos import DispositivoEletronico

# TODO: adicionar rastreamento de metodo aplicado
# TODO: criar relatorio de impacto por metodo

class MetodoTratamento(ABC):
    
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
    
    def __init__(self):
        super().__init__(custo_base_por_kg=15.0, reducao_impacto_percentual=80.0)

    def obter_nome(self) -> str:
        return "Reciclagem"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        custo_total = 0.0
        
        for dispositivo in dispositivos:
            peso = dispositivo.peso_kg
            custo_base = peso * self._custo_base_por_kg
            
            tipo = dispositivo.obter_tipo()
            if "Celular" in tipo:
                custo_base *= 1.3
            elif "Computador" in tipo:
                custo_base *= 1.2
                
            custo_total += custo_base
            
        return round(custo_total, 2)

    def calcular_impacto_ambiental(
        self, 
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        impacto_total = 0.0
        
        for dispositivo in dispositivos:
            impacto_original = dispositivo.calcular_impacto_ambiental()
            impacto_liquido = impacto_original * (1 - self._reducao_impacto_percentual / 100)
            impacto_total += impacto_liquido
            
        return round(impacto_total, 2)


class Reuso(MetodoTratamento):
    
    def __init__(self):
        super().__init__(custo_base_por_kg=8.0, reducao_impacto_percentual=95.0)

    def obter_nome(self) -> str:
        return "Reuso"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        custo_total = 0.0
        
        for dispositivo in dispositivos:
            peso = dispositivo.peso_kg
            custo_base = peso * self._custo_base_por_kg
            
            idade = 2026 - dispositivo.ano_fabricacao
            if idade < 3:
                custo_base *= 1.5
            elif idade < 5:
                custo_base *= 1.2
                
            custo_total += custo_base
            
        return round(custo_total, 2)

    def calcular_impacto_ambiental(
        self, 
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        impacto_total = 0.0
        
        for dispositivo in dispositivos:
            impacto_original = dispositivo.calcular_impacto_ambiental()
            impacto_liquido = impacto_original * (1 - self._reducao_impacto_percentual / 100)
            impacto_total += impacto_liquido
            
        return round(impacto_total, 2)


class DescarteControlado(MetodoTratamento):
    
    def __init__(self):
        super().__init__(custo_base_por_kg=25.0, reducao_impacto_percentual=40.0)

    def obter_nome(self) -> str:
        return "Descarte Controlado"

    def calcular_custo(self, dispositivos: List[DispositivoEletronico]) -> float:
        custo_total = 0.0
        
        for dispositivo in dispositivos:
            peso = dispositivo.peso_kg
            custo_base = peso * self._custo_base_por_kg
            
            periculosidade = dispositivo.categoria_periculosidade.value
            custo_base *= (1 + periculosidade * 0.2)
            
            custo_total += custo_base
            
        return round(custo_total, 2)

    def calcular_impacto_ambiental(
        self, 
        dispositivos: List[DispositivoEletronico]
    ) -> float:
        impacto_total = 0.0
        
        for dispositivo in dispositivos:
            impacto_original = dispositivo.calcular_impacto_ambiental()
            impacto_liquido = impacto_original * (1 - self._reducao_impacto_percentual / 100)
            impacto_total += impacto_liquido
            
        return round(impacto_total, 2)
