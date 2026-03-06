"""
Modulo de dispositivos eletronicos.

Este modulo define a hierarquia de classes para dispositivos, utilizando
heranca e polimorfismo para gerenciar atributos, impacto ambiental e
valor de revenda.
"""

from abc import ABC, abstractmethod

class DispositivoEletronico(ABC):
    """
    Classe abstrata base para dispositivos eletrônicos.

    Define a interface comum que todas as subclasses devem implementar.
    Fornece validações básicas no construtor e propriedades de acesso aos atributos.
    """

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):
        """
        Inicializa um dispositivo eletrônico.

        Args:
            id: Identificador único.
            nome: Nome descritivo.
            peso_kg: Peso em kg (> 0).
            marca: Nome do fabricante.
            modelo: Designação do modelo.

        Raises:
            ValueError: Se o peso <= 0 ou marca/modelo forem inválidos.
        """
        if peso_kg <= 0:
            raise ValueError("O peso deve ser um valor positivo.")
        
        for valor, nome_campo in [(marca, "marca"), (modelo, "modelo")]:
            if not isinstance(valor, str) or len(valor) > 100:
                raise ValueError(f"{nome_campo} deve ser uma string com até 100 caracteres.")

        self._id = id
        self._nome = nome
        self._peso_kg = peso_kg
        self._marca = marca
        self._modelo = modelo

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
    def marca(self) -> str:
        return self._marca

    @property
    def modelo(self) -> str:
        return self._modelo

    @abstractmethod
    def obter_tipo(self) -> str:
        """Retorna o tipo do dispositivo."""
        pass

    @abstractmethod
    def calcular_impacto_ambiental(self) -> float:
        """Calcula o impacto ambiental do dispositivo."""
        pass

    @abstractmethod
    def calcular_valor_revenda(self) -> float:
        """Calcula o valor de revenda estimado."""
        pass

    def __str__(self) -> str:
        return f"{self.obter_tipo()}: {self._nome} ({self._peso_kg}kg)"


class Celular(DispositivoEletronico):
    """Implementação para dispositivos do tipo Celular."""

    def obter_tipo(self) -> str: return "Celular"

    def calcular_impacto_ambiental(self) -> float:
        return self._peso_kg * 5.0

    def calcular_valor_revenda(self) -> float:
        return self._peso_kg * 10.0


class Computador(DispositivoEletronico):
    """Implementação para dispositivos do tipo Computador."""

    def obter_tipo(self) -> str: return "Computador"

    def calcular_impacto_ambiental(self) -> float:
        return self._peso_kg * 15.0

    def calcular_valor_revenda(self) -> float:
        return self._peso_kg * 25.0


class Eletrodomestico(DispositivoEletronico):
    """Implementação para dispositivos do tipo Eletrodoméstico."""

    def obter_tipo(self) -> str:
        return "Eletrodomestico"

    def calcular_impacto_ambiental(self) -> float:
        return self._peso_kg * 8.0

    def calcular_valor_revenda(self) -> float:
        return self._peso_kg * 15.0