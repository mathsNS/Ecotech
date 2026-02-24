# A- modulo de dispositivos eletronicos
# responsavel por gerenciar diferentes tipos de dispositivos
# importante rpra herança e polimorfismo

from abc import ABC, abstractmethod

# A- Validacoes de marca e modelo implementadas no __init__  # ABNER 24/02
# A- Calculo de valor de revenda implementado em cada subclasse  # ABNER 24/02


class DispositivoEletronico(ABC):
    # A- classe abstrata base para todos os dispositivos
    # define interface comum que todas as subclasses devem implementar

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):  # abner 10/02
        # A- validacoes basicas dos parametros
        if peso_kg <= 0:
            raise ValueError("peso deve ser positivo")

        # A- Validacoes de marca e modelo  # ABNER 24/02
        if not isinstance(marca, str):
            raise ValueError("marca deve ser uma string")  # ABNER 24/02
        if marca and len(marca.strip()) == 0:
            raise ValueError(
                "marca nao pode conter apenas espacos")  # ABNER 24/02
        if len(marca) > 100:
            raise ValueError(
                "marca nao pode ter mais de 100 caracteres")  # ABNER 24/02

        if not isinstance(modelo, str):
            raise ValueError("modelo deve ser uma string")  # ABNER 24/02
        if modelo and len(modelo.strip()) == 0:
            raise ValueError(
                "modelo nao pode conter apenas espacos")  # ABNER 24/02
        if len(modelo) > 100:
            raise ValueError(
                "modelo nao pode ter mais de 100 caracteres")  # ABNER 24/02

        # A- atributos privados (encapsulamento)
        self._id = id
        self._nome = nome
        self._peso_kg = peso_kg
        self._marca = marca  # abner 10/02
        self._modelo = modelo  # abner 10/02

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

    @property
    def marca(self) -> str:  # abner 10/02
        return self._marca

    @property
    def modelo(self) -> str:  # abner 10/02
        return self._modelo

    # A- metodo abstrato que cada tipo deve implementar (polimorfismo)
    @abstractmethod
    def obter_tipo(self) -> str:
        pass

    @abstractmethod
    def calcular_impacto_ambiental(self) -> float:
        # A- cada tipo de dispositivo tem seu proprio impacto
        pass

    @abstractmethod
    def calcular_valor_revenda(self) -> float:  # abner 10/02
        # A- calcula o valor de revenda baseado no tipo e condicao do dispositivo
        pass

    def __str__(self) -> str:
        return f"{self.obter_tipo()}: {self._nome} ({self._peso_kg}kg)"


class Celular(DispositivoEletronico):
    # A- implementacao concreta para celulares
    # herda de DispositivoEletronico

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):  # abner 10/02
        super().__init__(id, nome, peso_kg, marca, modelo)

    def obter_tipo(self) -> str:
        return "Celular"

    def calcular_impacto_ambiental(self) -> float:
        # A- celular tem impacto fixo de 5.0 por kg
        return self._peso_kg * 5.0

    def calcular_valor_revenda(self) -> float:  # abner 10/02
        # A- valor de revenda para celular: 10% do peso em kg
        return self._peso_kg * 10.0


class Computador(DispositivoEletronico):
    # A- implementacao para computadores

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):  # abner 10/02
        super().__init__(id, nome, peso_kg, marca, modelo)

    def obter_tipo(self) -> str:
        return "Computador"

    def calcular_impacto_ambiental(self) -> float:
        # A- computadores tem impacto de 15.0 por kg (maior que celular)
        return self._peso_kg * 15.0

    def calcular_valor_revenda(self) -> float:  # abner 10/02
        # A- valor de revenda para computador: 25% do peso em kg (maior valor agregado)
        return self._peso_kg * 25.0


class Eletrodomestico(DispositivoEletronico):
    # A- implementacao para eletrodomesticos

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):  # abner 10/02
        super().__init__(id, nome, peso_kg, marca, modelo)

    def obter_tipo(self) -> str:
        return "Eletrodomestico"

    def calcular_impacto_ambiental(self) -> float:
        # A- eletrodomesticos tem impacto medio de 8.0 por kg
        return self._peso_kg * 8.0

    def calcular_valor_revenda(self) -> float:  # abner 10/02
        # A- valor de revenda para eletrodomestico: 15% do peso em kg
        return self._peso_kg * 15.0
