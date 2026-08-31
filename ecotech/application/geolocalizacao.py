"""Abstrações de localização e cálculo de distância."""

from abc import ABC, abstractmethod
from math import asin, cos, radians, sin, sqrt

from ..domain.logistica import Coordenadas


class Geolocalizador(ABC):
    @abstractmethod
    def localizar(self, endereco: str, latitude=None, longitude=None) -> Coordenadas:
        """Obtém coordenadas para um endereço."""


class GeolocalizadorCoordenadasInformadas(Geolocalizador):
    """MVP: valida coordenadas fornecidas pelo navegador ou formulário."""

    def localizar(self, endereco: str, latitude=None, longitude=None) -> Coordenadas:
        if not endereco or not endereco.strip():
            raise ValueError("endereço de coleta é obrigatório")
        if latitude in (None, '') or longitude in (None, ''):
            raise ValueError(
                "não foi possível obter a localização; informe latitude e longitude"
            )
        try:
            return Coordenadas(float(latitude), float(longitude))
        except (TypeError, ValueError) as exc:
            raise ValueError("coordenadas de coleta inválidas") from exc


class CalculadorDistancia(ABC):
    @abstractmethod
    def calcular_km(self, origem: Coordenadas, destino: Coordenadas) -> float:
        """Calcula a distância em quilômetros entre dois pontos."""


class DistanciaHaversine(CalculadorDistancia):
    RAIO_TERRA_KM = 6371.0088

    def calcular_km(self, origem: Coordenadas, destino: Coordenadas) -> float:
        lat1, lon1 = radians(origem.latitude), radians(origem.longitude)
        lat2, lon2 = radians(destino.latitude), radians(destino.longitude)
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        )
        return round(2 * self.RAIO_TERRA_KM * asin(sqrt(a)), 6)
