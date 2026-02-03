# A- modulo de dispositivos eletronicos
# responsavel por gerenciar diferentes tipos de dispositivos
# importante rpra herança e polimorfismo

from abc import ABC, abstractmethod

# A- TODO: adicionar validacao de marca e modelo
# A- TODO: implementar calculo de valor de revenda


class DispositivoEletronico(ABC):
    # A- classe abstrata base para todos os dispositivos
    # define interface comum que todas as subclasses devem implementar
    
    def __init__(self, id: str, nome: str, peso_kg: float):
        # A- validacoes basicas dos parametros
        if peso_kg <= 0:
            raise ValueError("peso deve ser positivo")
            
        # A- atributos privados (encapsulamento)
        self._id = id
        self._nome = nome
        self._peso_kg = peso_kg

    # A- properties para acesso controlado aos atributos
    @property
    def id(self) -> str:
        return self._id

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def peso_kg(self) -> float:
        return self._peso_kg

    # A- metodo abstrato que cada tipo deve implementar (polimorfismo)
    @abstractmethod
    def obter_tipo(self) -> str:
        pass

    @abstractmethod
    def calcular_impacto_ambiental(self) -> float:
        # A- cada tipo de dispositivo tem seu proprio impacto
        pass

    def __str__(self) -> str:
        return f"{self.obter_tipo()}: {self._nome} ({self._peso_kg}kg)"


class Celular(DispositivoEletronico):
    # A- implementacao concreta para celulares
    # herda de DispositivoEletronico
    
    def __init__(self, id: str, nome: str, peso_kg: float):
        super().__init__(id, nome, peso_kg)

    def obter_tipo(self) -> str:
        return "Celular"

    def calcular_impacto_ambiental(self) -> float:
        # A- celular tem impacto fixo de 5.0 por kg
        return self._peso_kg * 5.0


class Computador(DispositivoEletronico):
    # A- implementacao para computadores
    
    def __init__(self, id: str, nome: str, peso_kg: float):
        super().__init__(id, nome, peso_kg)

    def obter_tipo(self) -> str:
        return "Computador"

    def calcular_impacto_ambiental(self) -> float:
        # A- computadores tem impacto de 15.0 por kg (maior que celular)
        return self._peso_kg * 15.0


class Eletrodomestico(DispositivoEletronico):
    # A- implementacao para eletrodomesticos
    
    def __init__(self, id: str, nome: str, peso_kg: float):
        super().__init__(id, nome, peso_kg)

    def obter_tipo(self) -> str:
        return "Eletrodomestico"

    def calcular_impacto_ambiental(self) -> float:
        # A- eletrodomesticos tem impacto medio de 8.0 por kg
        return self._peso_kg * 8.0
