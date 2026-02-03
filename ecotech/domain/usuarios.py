from abc import ABC, abstractmethod
from datetime import datetime
import re

# TODO: adicionar sistema de notificacoes
# TODO: implementar historico de acoes

class Usuario(ABC):
    
    def __init__(self, id: str, nome: str, email: str):
        self._validar_nome(nome)
        self._validar_email(email)
        
        self._id = id
        self._nome = nome
        self._email = email
        self._data_cadastro = datetime.now()
        self._ativo = True

    @property
    def id(self) -> str:
        return self._id

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str):
        self._validar_nome(valor)
        self._nome = valor

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str):
        self._validar_email(valor)
        self._email = valor

    @property
    def data_cadastro(self) -> datetime:
        return self._data_cadastro

    @property
    def ativo(self) -> bool:
        return self._ativo

    def ativar(self):
        self._ativo = True

    def desativar(self):
        self._ativo = False

    @staticmethod
    def _validar_nome(nome: str):
        if not nome or len(nome.strip()) < 3:
            raise ValueError("nome deve ter pelo menos 3 caracteres")

    @staticmethod
    def _validar_email(email: str):
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(padrao, email):
            raise ValueError("email invalido")

    @abstractmethod
    def pode_solicitar_descarte(self) -> bool:
        pass

    @abstractmethod
    def obter_tipo(self) -> str:
        pass

    def __str__(self) -> str:
        return f"{self.obter_tipo()}: {self._nome} ({self._email})"


class Cidadao(Usuario):
    
    MAX_SOLICITACOES_ATIVAS = 5

    def __init__(self, id: str, nome: str, email: str, cpf: str):
        super().__init__(id, nome, email)
        self._cpf = cpf
        self._solicitacoes_ativas = 0
        self._pontos_acumulados = 0

    @property
    def cpf(self) -> str:
        return self._cpf

    @property
    def pontos_acumulados(self) -> int:
        return self._pontos_acumulados

    def adicionar_pontos(self, pontos: int):
        if pontos > 0:
            self._pontos_acumulados += pontos

    def incrementar_solicitacoes_ativas(self):
        self._solicitacoes_ativas += 1

    def decrementar_solicitacoes_ativas(self):
        if self._solicitacoes_ativas > 0:
            self._solicitacoes_ativas -= 1

    def pode_solicitar_descarte(self) -> bool:
        return (
            self.ativo 
            and self._solicitacoes_ativas < self.MAX_SOLICITACOES_ATIVAS
        )

    def obter_tipo(self) -> str:
        return "Cidadao"


class Empresa(Usuario):
    
    def __init__(
        self, 
        id: str, 
        nome: str, 
        email: str, 
        cnpj: str,
        razao_social: str
    ):
        super().__init__(id, nome, email)
        self._cnpj = cnpj
        self._razao_social = razao_social
        self._limite_mensal_kg = 1000.0
        self._descartado_mes_atual = 0.0

    @property
    def cnpj(self) -> str:
        return self._cnpj

    @property
    def razao_social(self) -> str:
        return self._razao_social

    @property
    def limite_mensal_kg(self) -> float:
        return self._limite_mensal_kg

    def definir_limite_mensal(self, limite: float):
        if limite > 0:
            self._limite_mensal_kg = limite

    def registrar_descarte_kg(self, peso: float):
        self._descartado_mes_atual += peso

    def resetar_contador_mensal(self):
        self._descartado_mes_atual = 0.0

    def pode_solicitar_descarte(self) -> bool:
        return self.ativo and self._descartado_mes_atual < self._limite_mensal_kg

    def obter_tipo(self) -> str:
        return "Empresa"


class Administrador(Usuario):
    
    def __init__(
        self, 
        id: str, 
        nome: str, 
        email: str,
        nivel_acesso: int = 1
    ):
        super().__init__(id, nome, email)
        self._nivel_acesso = max(1, min(nivel_acesso, 3))
        self._pode_gerenciar_usuarios = nivel_acesso >= 2

    @property
    def nivel_acesso(self) -> int:
        return self._nivel_acesso

    @property
    def pode_gerenciar_usuarios(self) -> bool:
        return self._pode_gerenciar_usuarios

    def pode_solicitar_descarte(self) -> bool:
        return False

    def obter_tipo(self) -> str:
        return f"Administrador (Nivel {self._nivel_acesso})"
