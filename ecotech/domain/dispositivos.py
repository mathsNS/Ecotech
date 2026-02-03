from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict

# TODO: adicionar validacao de marca e modelo
# TODO: implementar calculo de valor de revenda

class CategoriaPericulosidade(Enum):
    BAIXA = 1
    MEDIA = 2
    ALTA = 3
    MUITO_ALTA = 4


class DispositivoEletronico(ABC):
    
    FATOR_IMPACTO_BASE = 10.0

    def __init__(
        self,
        id: str,
        nome: str,
        peso_kg: float,
        ano_fabricacao: int,
        categoria_periculosidade: CategoriaPericulosidade
    ):
        if peso_kg <= 0:
            raise ValueError("Peso deve ser positivo")
        if ano_fabricacao < 1900 or ano_fabricacao > 2026:
            raise ValueError("Ano de fabricacao invalido")
            
        self._id = id
        self._nome = nome
        self._peso_kg = peso_kg
        self._ano_fabricacao = ano_fabricacao
        self._categoria_periculosidade = categoria_periculosidade

    @property
    def id(self) -> str:
        return self._id

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def peso_kg(self) -> float:
        return self._peso_kg

    @property
    def ano_fabricacao(self) -> int:
        return self._ano_fabricacao

    @property
    def categoria_periculosidade(self) -> CategoriaPericulosidade:
        return self._categoria_periculosidade

    @abstractmethod
    def obter_tipo(self) -> str:
        pass

    @abstractmethod
    def obter_fator_impacto_especifico(self) -> float:
        pass

    @abstractmethod
    def obter_materiais_perigosos(self) -> Dict[str, float]:
        pass

    def calcular_impacto_ambiental(self) -> float:
        impacto = self._peso_kg * self.FATOR_IMPACTO_BASE
        impacto *= self.obter_fator_impacto_especifico()
        impacto *= self._categoria_periculosidade.value
        
        idade = 2026 - self._ano_fabricacao
        fator_idade = 1.0 + (idade * 0.05)
        impacto *= fator_idade
        
        return round(impacto, 2)

    def __str__(self) -> str:
        return f"{self.obter_tipo()}: {self._nome} ({self._peso_kg}kg)"


class Celular(DispositivoEletronico):

    def __init__(
        self,
        id: str,
        nome: str,
        peso_kg: float,
        ano_fabricacao: int,
        tem_bateria: bool = True
    ):
        super().__init__(
            id, nome, peso_kg, ano_fabricacao, 
            CategoriaPericulosidade.ALTA
        )
        self._tem_bateria = tem_bateria

    @property
    def tem_bateria(self) -> bool:
        return self._tem_bateria

    def obter_tipo(self) -> str:
        return "Celular"

    def obter_fator_impacto_especifico(self) -> float:
        return 2.5 if self._tem_bateria else 2.0

    def obter_materiais_perigosos(self) -> Dict[str, float]:
        return {
            "litio": self._peso_kg * 0.15,
            "chumbo": self._peso_kg * 0.05,
            "mercurio": self._peso_kg * 0.001
        }


class Computador(DispositivoEletronico):

    def __init__(
        self,
        id: str,
        nome: str,
        peso_kg: float,
        ano_fabricacao: int,
        tipo_computador: str = "desktop"
    ):
        super().__init__(
            id, nome, peso_kg, ano_fabricacao,
            CategoriaPericulosidade.ALTA
        )
        self._tipo_computador = tipo_computador

    @property
    def tipo_computador(self) -> str:
        return self._tipo_computador

    def obter_tipo(self) -> str:
        return f"Computador ({self._tipo_computador})"

    def obter_fator_impacto_especifico(self) -> float:
        fatores = {
            "desktop": 2.0,
            "notebook": 2.2,
            "servidor": 2.8
        }
        return fatores.get(self._tipo_computador, 2.0)

    def obter_materiais_perigosos(self) -> Dict[str, float]:
        return {
            "chumbo": self._peso_kg * 0.08,
            "mercurio": self._peso_kg * 0.002,
            "cadmio": self._peso_kg * 0.01
        }


class Eletrodomestico(DispositivoEletronico):

    def __init__(
        self,
        id: str,
        nome: str,
        peso_kg: float,
        ano_fabricacao: int,
        categoria: str,
        tem_gas_refrigerante: bool = False
    ):
        periculosidade = (
            CategoriaPericulosidade.MUITO_ALTA if tem_gas_refrigerante 
            else CategoriaPericulosidade.MEDIA
        )
        
        super().__init__(
            id, nome, peso_kg, ano_fabricacao, periculosidade
        )
        self._categoria = categoria
        self._tem_gas_refrigerante = tem_gas_refrigerante

    @property
    def categoria(self) -> str:
        return self._categoria

    @property
    def tem_gas_refrigerante(self) -> bool:
        return self._tem_gas_refrigerante

    def obter_tipo(self) -> str:
        return f"Eletrodomestico ({self._categoria})"

    def obter_fator_impacto_especifico(self) -> float:
        if self._tem_gas_refrigerante:
            return 3.0
        
        fatores = {
            "geladeira": 2.5,
            "tv": 1.8,
            "micro-ondas": 1.5
        }
        return fatores.get(self._categoria, 1.5)

    def obter_materiais_perigosos(self) -> Dict[str, float]:
        materiais = {
            "chumbo": self._peso_kg * 0.03,
            "mercurio": self._peso_kg * 0.001,
        }
        
        if self._tem_gas_refrigerante:
            materiais["cfc"] = self._peso_kg * 0.02
            
        return materiais
