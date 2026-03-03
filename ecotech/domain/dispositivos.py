# A- modulo de dispositivos eletronicos
# responsavel por gerenciar diferentes tipos de dispositivos
# importante rpra herança e polimorfismo

from abc import ABC, abstractmethod

# A- TODO: adicionar validacao de marca e modelo
# A- TODO: implementar calculo de valor de revenda


class DispositivoEletronico(ABC):
    """Classe abstrata base para dispositivos eletrônicos.

    Define a interface comum que todas as subclasses devem implementar.
    Fornece validações básicas no construtor e propriedades de acesso
    aos atributos.
    """

    # A- classe abstrata base para todos os dispositivos
    # define interface comum que todas as subclasses devem implementar

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):  # abner 10/02
        """Inicializa o dispositivo eletrônico.

        Args:
        ----------
        id : str
            Identificador único do dispositivo.
        nome : str
            Nome descritivo do dispositivo.
        peso_kg : float
            Peso em quilos (deve ser positivo).
        marca : str, opcional
            Nome da marca (padrão vazio).
        modelo : str, opcional
            Designação do modelo (padrão vazio).

        ------
        Raises:
        ------

            ValueError: Se o peso for menor ou igual a zero.
            ValueError: Se marca ou modelo não forem strings válidas
                        ou ultrapassarem 100 caracteres.
        """
        # A- validacoes basicas dos parametros
        if peso_kg <= 0:
            raise ValueError("peso deve ser positivo")
        if marca and not isinstance(marca, str):  # abner 10/02
            raise ValueError("marca deve ser uma string")
        if modelo and not isinstance(modelo, str):  # abner 10/02
            raise ValueError("modelo deve ser uma string")

        # A- atributos privados (encapsulamento)
        self._id = id
        self._nome = nome
        self._peso_kg = peso_kg
        self._marca = marca  # abner 10/02
        self._modelo = modelo  # abner 10/02

    # A- properties para acesso controlado aos atributos
    @property
    def id(self) -> str:
        """Retorna o identificador único do dispositivo."""
        return self._id

    @property
    def nome(self) -> str:
        """Retorna o nome do dispositivo."""
        return self._nome

    @property
    def peso_kg(self) -> float:
        """Retorna o peso do dispositivo em quilogramas."""
        return self._peso_kg

    @property
    def marca(self) -> str:  # abner 10/02
        """Retorna o nome da marca do dispositivo."""
        return self._marca

    @property
    def modelo(self) -> str:  # abner 10/02
        """Retorna a designação do modelo do dispositivo."""
        return self._modelo

    # A- metodo abstrato que cada tipo deve implementar (polimorfismo)
    @abstractmethod
    def obter_tipo(self) -> str:
        """Retorna o nome do tipo do dispositivo para apresentação.

        Cada subclasse deve implementar isto com seu próprio tipo
        (por exemplo, "Celular", "Computador").
        """
        pass

    @abstractmethod
    def calcular_impacto_ambiental(self) -> float:
        """Calcula e retorna o impacto ambiental do dispositivo.

        A implementação é específica de cada tipo, geralmente baseada no
        peso ou outras características.
        """
        # A- cada tipo de dispositivo tem seu proprio impacto
        pass

    @abstractmethod
    def calcular_valor_revenda(self) -> float:  # abner 10/02
        """Calcula e retorna o valor de revenda do dispositivo.

        A fórmula é determinada pela subclasse concreta e pode considerar
        peso, tipo e condição.
        """
        # A- calcula o valor de revenda baseado no tipo e condicao do dispositivo
        pass

    def __str__(self) -> str:
        """Retorna uma representação legível do dispositivo."""
        return f"{self.obter_tipo()}: {self._nome} ({self._peso_kg}kg)"


class Celular(DispositivoEletronico):
    """Implementação concreta de dispositivo representando um celular.

    Herda de :class:`DispositivoEletronico` e provê comportamento específico
    para impacto e valor de revenda.
    """

    # A- implementacao concreta para celulares
    # herda de DispositivoEletronico

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):  # abner 10/02
        super().__init__(id, nome, peso_kg, marca, modelo)

    def obter_tipo(self) -> str:
        """Retorna a string "Celular" como tipo do dispositivo."""
        return "Celular"

    def calcular_impacto_ambiental(self) -> float:
        """Calcula impacto ambiental do celular: 5.0 por kg."""
        # A- celular tem impacto fixo de 5.0 por kg
        return self._peso_kg * 5.0

    def calcular_valor_revenda(self) -> float:  # abner 10/02
        """Calcula valor de revenda do celular: 10% do peso."""
        # A- valor de revenda para celular: 10% do peso em kg
        return self._peso_kg * 10.0


class Computador(DispositivoEletronico):
    """Implementação concreta de dispositivo representando um computador."""

    # A- implementacao para computadores

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):  # abner 10/02
        super().__init__(id, nome, peso_kg, marca, modelo)

    def obter_tipo(self) -> str:
        """Retorna a string "Computador" como tipo."""
        return "Computador"

    def calcular_impacto_ambiental(self) -> float:
        """Calcula impacto ambiental do computador: 15.0 por kg."""
        # A- computadores tem impacto de 15.0 por kg (maior que celular)
        return self._peso_kg * 15.0

    def calcular_valor_revenda(self) -> float:  # abner 10/02
        """Calcula valor de revenda do computador: 25% do peso."""
        # A- valor de revenda para computador: 25% do peso em kg (maior valor agregado)
        return self._peso_kg * 25.0


class Eletrodomestico(DispositivoEletronico):
    """Implementação concreta de dispositivo para eletrodomésticos."""

    # A- implementacao para eletrodomesticos

    def __init__(self, id: str, nome: str, peso_kg: float, marca: str = "", modelo: str = ""):  # abner 10/02
        super().__init__(id, nome, peso_kg, marca, modelo)

    def obter_tipo(self) -> str:
        """Retorna a string "Eletrodomestico" como tipo."""
        return "Eletrodomestico"

    def calcular_impacto_ambiental(self) -> float:
        """Calcula impacto ambiental do eletrodoméstico: 8.0 por kg."""
        # A- eletrodomesticos tem impacto medio de 8.0 por kg
        return self._peso_kg * 8.0

    def calcular_valor_revenda(self) -> float:  # abner 10/02
        """Calcula valor de revenda do eletrodoméstico: 15% do peso."""
        # A- valor de revenda para eletrodomestico: 15% do peso em kg
        return self._peso_kg * 15.0
