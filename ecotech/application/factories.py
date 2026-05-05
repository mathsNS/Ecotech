"""Módulo de Factories para criação de objetos do domínio.

Centraliza a instanciação de dispositivos, usuários, métodos de tratamento
e pontos de coleta, aplicando o padrão Factory para desacoplar a lógica
de criação do restante do sistema.
"""

from typing import Dict, Any

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
from ..domain.descarte import PontoColeta
from ..domain.estados import (
    Solicitado, Coletado, EmProcessamento,
    Reciclado, Reutilizado, Descartado, Cancelado
)


class DispositivoFactory:
    """Factory para criação de dispositivos eletrônicos.

    Centraliza a instanciação de diferentes tipos de dispositivos,
    permitindo criar objetos sem expor a lógica de construção.
    """

    @staticmethod
    def criar_celular(id: str, nome: str, peso_kg: float) -> Celular:
        """Cria uma instância de Celular."""
        return Celular(id, nome, peso_kg)

    @staticmethod
    def criar_computador(id: str, nome: str, peso_kg: float) -> Computador:
        """Cria uma instância de Computador."""
        return Computador(id, nome, peso_kg)

    @staticmethod
    def criar_eletrodomestico(id: str, nome: str, peso_kg: float) -> Eletrodomestico:
        """Cria uma instância de Eletrodoméstico."""
        return Eletrodomestico(id, nome, peso_kg)

    @staticmethod
    def criar_dispositivo(tipo: str, dados: Dict[str, Any]) -> DispositivoEletronico:
        """Cria um dispositivo do tipo especificado a partir de um dicionário de dados."""
        tipo_lower = tipo.lower()
        if tipo_lower == "celular":
            return DispositivoFactory.criar_celular(**dados)
        elif tipo_lower == "computador":
            return DispositivoFactory.criar_computador(**dados)
        elif tipo_lower == "eletrodomestico":
            return DispositivoFactory.criar_eletrodomestico(**dados)
        else:
            raise ValueError(f"tipo de dispositivo invalido: {tipo}")


class UsuarioFactory:
    """Factory para criação de usuários do sistema.

    Centraliza a instanciação de cidadãos, empresas e administradores.
    """

    @staticmethod
    def criar_cidadao(id: str, nome: str, email: str, cpf: str) -> Cidadao:
        """Cria uma instância de Cidadão."""
        return Cidadao(id, nome, email, cpf)

    @staticmethod
    def criar_empresa(
        id: str,
        nome: str,
        email: str,
        cnpj: str,
        razao_social: str
    ) -> Empresa:
        """Cria uma instância de Empresa."""
        return Empresa(id, nome, email, cnpj, razao_social)

    @staticmethod
    def criar_administrador(
        id: str,
        nome: str,
        email: str,
        nivel_acesso: int = 1
    ) -> Administrador:
        """Cria uma instância de Administrador."""
        return Administrador(id, nome, email, nivel_acesso)

    @staticmethod
    def criar_usuario(tipo: str, dados: Dict[str, Any]) -> Usuario:
        """Cria um usuário do tipo especificado a partir de um dicionário de dados."""
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
    """Factory para criação de métodos de tratamento ecológico.

    Cria instâncias das estratégias de tratamento (padrão Strategy).
    """

    @staticmethod
    def criar_reciclagem() -> Reciclagem:
        """Cria uma instância de Reciclagem."""
        return Reciclagem()

    @staticmethod
    def criar_reuso() -> Reuso:
        """Cria uma instância de Reuso."""
        return Reuso()

    @staticmethod
    def criar_descarte_controlado() -> DescarteControlado:
        """Cria uma instância de DescarteControlado."""
        return DescarteControlado()

    @staticmethod
    def criar_metodo(tipo: str) -> MetodoTratamento:
        """Cria um método de tratamento do tipo especificado."""
        tipo_lower = tipo.lower()

        if tipo_lower == "reciclagem":
            return MetodoTratamentoFactory.criar_reciclagem()
        elif tipo_lower == "reuso":
            return MetodoTratamentoFactory.criar_reuso()
        elif tipo_lower == "descarte_controlado":
            return MetodoTratamentoFactory.criar_descarte_controlado()
        else:
            raise ValueError(f"tipo de metodo invalido: {tipo}")


class PontoColetaFactory:
    """Factory para criação de pontos de coleta.

    Centraliza a instanciação de pontos de coleta a partir
    de parâmetros individuais ou dicionário de dados.
    """

    @staticmethod
    def criar_ponto_coleta(
        id: str,
        nome: str,
        endereco: str,
        latitude: float,
        longitude: float,
        capacidade_kg: float = 1000.0
    ) -> PontoColeta:
        """Cria uma instância de PontoColeta."""
        return PontoColeta(id, nome, endereco, latitude, longitude, capacidade_kg)

    @staticmethod
    def criar_ponto(dados: Dict[str, Any]) -> PontoColeta:
        """Cria um ponto de coleta a partir de um dicionário de dados."""
        return PontoColetaFactory.criar_ponto_coleta(**dados)


class EstadoFactory:
    """Converte strings do banco em instâncias de estado."""

    _MAPA = {
        'SOLICITADO': Solicitado,
        'COLETADO': Coletado,
        'EM_PROCESSAMENTO': EmProcessamento,
        'RECICLADO': Reciclado,
        'REUTILIZADO': Reutilizado,
        'DESCARTADO': Descartado,
        'CANCELADO': Cancelado,
    }

    @staticmethod
    def criar_do_banco(nome_estado: str):
        """Retorna instância de estado pelo nome. Usa Solicitado como fallback."""
        classe = EstadoFactory._MAPA.get(nome_estado, Solicitado)
        return classe()
