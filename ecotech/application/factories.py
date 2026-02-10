from typing import Dict, Any

# A- TODO: adicionar factory para pontos de coleta
# M- TODO: validar dados antes de criar objetos

from ..domain.dispositivos import (
    DispositivoEletronico,
    Celular,
    Computador,
    Eletrodomestico
)
from ..domain.usuarios import Usuario, Cidadao, Empresa, Administrador
from ..domain.tratamento import (
    MetodoTratamento,
    Reciclagem,
    Reuso,
    DescarteControlado
)
from ..domain.descarte import PontoColeta  # abner 10/2


class DispositivoFactory:
    # A- factory para criar dispositivos
    # centraliza a criacao e facilita manutencao

    @staticmethod
    def criar_celular(id: str, nome: str, peso_kg: float) -> Celular:
        return Celular(id, nome, peso_kg)

    @staticmethod
    def criar_computador(id: str, nome: str, peso_kg: float) -> Computador:
        return Computador(id, nome, peso_kg)

    @staticmethod
    def criar_eletrodomestico(id: str, nome: str, peso_kg: float) -> Eletrodomestico:
        return Eletrodomestico(id, nome, peso_kg)

    @staticmethod
    def criar_dispositivo(tipo: str, dados: Dict[str, Any]) -> DispositivoEletronico:
        # A- metodo que escolhe qual tipo criar baseado no parametro
        tipo_lower = tipo.lower()
        print(f"[DEBUG] criando dispositivo tipo: {tipo_lower}")
        if tipo_lower == "celular":
            return DispositivoFactory.criar_celular(**dados)
        elif tipo_lower == "computador":
            return DispositivoFactory.criar_computador(**dados)
        elif tipo_lower == "eletrodomestico":
            return DispositivoFactory.criar_eletrodomestico(**dados)
        else:
            raise ValueError(f"tipo de dispositivo invalido: {tipo}")


class UsuarioFactory:
    # M- factory para criar usuarios

    @staticmethod
    def criar_cidadao(id: str, nome: str, email: str, cpf: str) -> Cidadao:
        return Cidadao(id, nome, email, cpf)

    @staticmethod
    def criar_empresa(
        id: str,
        nome: str,
        email: str,
        cnpj: str,
        razao_social: str
    ) -> Empresa:
        return Empresa(id, nome, email, cnpj, razao_social)

    @staticmethod
    def criar_administrador(
        id: str,
        nome: str,
        email: str,
        nivel_acesso: int = 1
    ) -> Administrador:
        return Administrador(id, nome, email, nivel_acesso)

    @staticmethod
    def criar_usuario(tipo: str, dados: Dict[str, Any]) -> Usuario:
        # M- metodo que escolhe qual tipo criar (genericao)
        tipo_lower = tipo.lower()

        if tipo_lower == "cidadao":
            return UsuarioFactory.criar_cidadao(**dados)
        elif tipo_lower == "empresa":
            return UsuarioFactory.criar_empresa(**dados)
        elif tipo_lower == "administrador":
            return UsuarioFactory.criar_administrador(**dados)
        else:
            raise ValueError(f"tipo de usuario invalido: {tipo}")


class MetodoTratamentoFactory:
    # factory para metodos de tratamento padrao strategy

    @staticmethod
    def criar_reciclagem() -> Reciclagem:
        return Reciclagem()

    @staticmethod
    def criar_reuso() -> Reuso:
        return Reuso()

    @staticmethod
    def criar_descarte_controlado() -> DescarteControlado:
        return DescarteControlado()

    @staticmethod
    def criar_metodo(tipo: str) -> MetodoTratamento:
        tipo_lower = tipo.lower()

        if tipo_lower == "reciclagem":
            return MetodoTratamentoFactory.criar_reciclagem()
        elif tipo_lower == "reuso":
            return MetodoTratamentoFactory.criar_reuso()
        elif tipo_lower == "descarte_controlado":
            return MetodoTratamentoFactory.criar_descarte_controlado()
        else:
            raise ValueError(f"tipo de metodo invalido: {tipo}")


class PontoColetaFactory:  # abner 10/02
    # A- factory para criar pontos de coleta
    # centraliza a criacao e facilita manutencao

    @staticmethod
    def criar_ponto_coleta(
        id: str,
        nome: str,
        endereco: str,
        latitude: float,
        longitude: float,
        capacidade_kg: float = 1000.0
    ) -> PontoColeta:
        return PontoColeta(id, nome, endereco, latitude, longitude, capacidade_kg)

    @staticmethod
    def criar_ponto(dados: Dict[str, Any]) -> PontoColeta:
        # A- metodo generico que cria ponto de coleta a partir de dicionario
        return PontoColetaFactory.criar_ponto_coleta(**dados)
