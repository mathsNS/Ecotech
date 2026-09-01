"""Abstrações de localização e cálculo de distância."""

from abc import ABC, abstractmethod
import json
from math import asin, cos, radians, sin, sqrt
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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


class GeolocalizadorPorCep(GeolocalizadorCoordenadasInformadas):
    """Resolve coordenadas internamente a partir de um CEP brasileiro."""

    URL = "https://brasilapi.com.br/api/cep/v2/{cep}"

    def consultar_cep(self, cep: str) -> dict:
        cep_limpo = re.sub(r"\D", "", cep or "")
        if len(cep_limpo) != 8:
            raise ValueError("informe um CEP válido com 8 dígitos")
        requisicao = Request(
            self.URL.format(cep=cep_limpo),
            headers={"User-Agent": "EcoTech/1.0"},
        )
        try:
            with urlopen(requisicao, timeout=5) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ValueError(
                "não foi possível consultar o CEP agora; tente novamente"
            ) from exc
        coordenadas = dados.get("location", {}).get("coordinates", {})
        try:
            dados["latitude"] = float(coordenadas["latitude"])
            dados["longitude"] = float(coordenadas["longitude"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "o CEP foi encontrado, mas ainda não possui localização disponível"
            ) from exc
        return dados

    def localizar(self, endereco: str, latitude=None, longitude=None,
                  cep: str = "") -> Coordenadas:
        if latitude not in (None, "") and longitude not in (None, ""):
            return super().localizar(endereco, latitude, longitude)
        dados = self.consultar_cep(cep)
        return Coordenadas(dados["latitude"], dados["longitude"])


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
