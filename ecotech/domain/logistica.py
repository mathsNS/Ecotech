"""Entidades de logística para o despacho de coletas domiciliares."""

from dataclasses import dataclass


def validar_coordenadas(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90:
        raise ValueError("latitude deve estar entre -90 e 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude deve estar entre -180 e 180")


@dataclass(frozen=True)
class Coordenadas:
    latitude: float
    longitude: float

    def __post_init__(self):
        validar_coordenadas(self.latitude, self.longitude)


class BaseOperacional:
    """Local físico de onde uma empresa despacha coletas domiciliares."""

    def __init__(
        self,
        id: str,
        empresa_id: str,
        nome: str,
        endereco: str,
        latitude: float,
        longitude: float,
        raio_atendimento_km: float,
        capacidade_kg: float,
        ocupacao_atual_kg: float = 0.0,
        realiza_coleta_domiciliar: bool = True,
        ativa: bool = True,
        ponto_coleta_id: str | None = None,
    ):
        if not id or not empresa_id:
            raise ValueError("base e empresa devem possuir identificadores")
        if not nome or not nome.strip():
            raise ValueError("nome da base é obrigatório")
        if not endereco or not endereco.strip():
            raise ValueError("endereço da base é obrigatório")
        validar_coordenadas(float(latitude), float(longitude))
        if raio_atendimento_km <= 0:
            raise ValueError("raio de atendimento deve ser positivo")
        if capacidade_kg <= 0:
            raise ValueError("capacidade deve ser positiva")
        if ocupacao_atual_kg < 0 or ocupacao_atual_kg > capacidade_kg:
            raise ValueError("ocupação deve estar entre zero e a capacidade")

        self._id = id
        self._empresa_id = empresa_id
        self._nome = nome.strip()
        self._endereco = endereco.strip()
        self._latitude = float(latitude)
        self._longitude = float(longitude)
        self._raio_atendimento_km = float(raio_atendimento_km)
        self._capacidade_kg = float(capacidade_kg)
        self._ocupacao_atual_kg = float(ocupacao_atual_kg)
        self._realiza_coleta_domiciliar = bool(realiza_coleta_domiciliar)
        self._ativa = bool(ativa)
        self._ponto_coleta_id = ponto_coleta_id

    @property
    def id(self): return self._id

    @property
    def empresa_id(self): return self._empresa_id

    @property
    def nome(self): return self._nome

    @property
    def endereco(self): return self._endereco

    @property
    def latitude(self): return self._latitude

    @property
    def longitude(self): return self._longitude

    @property
    def raio_atendimento_km(self): return self._raio_atendimento_km

    @property
    def capacidade_kg(self): return self._capacidade_kg

    @property
    def ocupacao_atual_kg(self): return self._ocupacao_atual_kg

    @property
    def realiza_coleta_domiciliar(self): return self._realiza_coleta_domiciliar

    @property
    def ativa(self): return self._ativa

    @property
    def ponto_coleta_id(self): return self._ponto_coleta_id

    @property
    def coordenadas(self) -> Coordenadas:
        return Coordenadas(self._latitude, self._longitude)

    def pertence_a(self, empresa_id: str) -> bool:
        return self._empresa_id == empresa_id
