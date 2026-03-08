"""
Módulo de Usuários

Responsável por gerenciar os diferentes tipos de usuários do sistema EcoTech,
incluindo cidadãos, empresas e administradores.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict
import re

class Usuario(ABC):
    """
    Classe abstrata base para todos os usuários do sistema.

    Esta classe define a interface comum, validações e comportamentos
    compartilhados entre cidadãos, empresas e administradores.
    """

    def __init__(self, id, nome, email) -> None:
        """
        Inicializa um novo usuário.
        """

        self._validar_nome(nome)
        self._validar_email(email)

        self._id: str = id
        self._nome: str = nome
        self._email: str = email
        self._data_cadastro: datetime = datetime.now()
        self._ativo: bool = True

        # Sistema de notificações
        self._notificacoes: List[str] = []

        # Sistema de histórico
        self._historico_acoes: List[Dict] = []

        self._registrar_acao("Usuário criado")

    # -------------------
    # PROPERTIES
    # -------------------

    @property
    def id(self) -> str:
        """Retorna o ID do usuário."""
        return self._id

    @property
    def nome(self) -> str:
        """Retorna o nome do usuário."""
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        """Define o nome do usuário com validação."""
        self._validar_nome(valor)
        self._nome = valor
        self._registrar_acao("Nome atualizado")

    @property
    def email(self) -> str:
        """Retorna o email do usuário."""
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        """Define o email do usuário com validação."""
        self._validar_email(valor)
        self._email = valor
        self._registrar_acao("Email atualizado")

    @property
    def ativo(self) -> bool:
        """Retorna o status do usuário."""
        return self._ativo

    @property
    def data_cadastro(self) -> datetime:
        """Retorna a data de cadastro."""
        return self._data_cadastro

    @property
    def notificacoes(self) -> List[str]:
        """Retorna todas as notificações."""
        return self._notificacoes.copy()

    @property
    def historico_acoes(self) -> List[Dict]:
        """Retorna o histórico de ações."""
        return self._historico_acoes.copy()

    # -------------------
    # CONTROLE DE STATUS
    # -------------------

    def ativar(self) -> None:
        """Ativa o usuário."""
        self._ativo = True
        self._registrar_acao("Usuário ativado")

    def desativar(self) -> None:
        """Desativa o usuário."""
        self._ativo = False
        self._registrar_acao("Usuário desativado")

    # ------------------------
    # SISTEMA DE NOTIFICAÇÕES
    # ------------------------

    def adicionar_notificacao(self, mensagem: str) -> None:
        """
        Adiciona uma nova notificação ao usuário.
        """

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        notificacao = f"[{timestamp}] {mensagem}"

        self._notificacoes.append(notificacao)
        self._registrar_acao("Notificação recebida")

    def limpar_notificacoes(self) -> None:
        """Remove todas as notificações."""
        self._notificacoes.clear()
        self._registrar_acao("Notificações limpas")

    # ------------
    # HISTÓRICO
    # ------------

    def _registrar_acao(self, descricao: str) -> None:
        """
        Registra uma ação no histórico.
        """

        self._historico_acoes.append(
            {
                "descricao": descricao,
                "data": datetime.now(),
            }
        )

    # ------------
    # VALIDAÇÕES
    # ------------

    @staticmethod
    def _validar_nome(nome: str) -> None:
        """Valida o nome."""
        if not nome or len(nome.strip()) < 3:
            raise ValueError("O nome deve ter pelo menos 3 caracteres.")

    @staticmethod
    def _validar_email(email: str) -> None:
        """Valida o email."""
        padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not re.match(padrao, email):
            raise ValueError("Email inválido.")

    # ------------------
    # MÉTODOS ABSTRATOS
    # ------------------

    @abstractmethod
    def pode_solicitar_descarte(self) -> bool:
        """Define se o usuário pode solicitar descarte."""
        pass

    @abstractmethod
    def obter_tipo(self) -> str:
        """Retorna o tipo do usuário."""
        pass

    # ---------------
    # REPRESENTAÇÃO
    # ---------------

    def __str__(self) -> str:
        return f"{self.obter_tipo()} - {self.nome} ({self.email})"

# ---------
# CIDADÃO
# ---------

class Cidadao(Usuario):
    """
    Representa um cidadão no sistema.

    Possui limite de solicitações ativas e sistema de pontuação.
    """

    MAX_SOLICITACOES_ATIVAS = 5

    def __init__(self, id, nome, email, cpf) -> None:
        super().__init__(id, nome, email)

        self._validar_cpf(cpf)

        self._cpf: str = cpf
        self._solicitacoes_ativas: int = 0
        self._pontos: int = 0

        self._registrar_acao("Cidadão criado")

    @staticmethod
    def _validar_cpf(cpf: str) -> None:
        """Valida formato básico do CPF."""
        padrao = r"^\d{11}$"

        if not re.match(padrao, cpf):
            raise ValueError("CPF deve conter 11 números.")

    @property
    def pontos(self) -> int:
        return self._pontos

    def adicionar_pontos(self, pontos: int) -> None:
        if pontos <= 0:
            raise ValueError("Pontos devem ser positivos.")

        self._pontos += pontos
        self._registrar_acao(f"{pontos} pontos adicionados")

    def incrementar_solicitacoes(self) -> None:
        if not self.pode_solicitar_descarte():
            raise Exception("Limite de solicitações atingido.")

        self._solicitacoes_ativas += 1
        self._registrar_acao("Solicitação criada")

    def decrementar_solicitacoes(self) -> None:
        if self._solicitacoes_ativas > 0:
            self._solicitacoes_ativas -= 1
            self._registrar_acao("Solicitação finalizada")

    def pode_solicitar_descarte(self) -> bool:
        return (
            self.ativo
            and self._solicitacoes_ativas < self.MAX_SOLICITACOES_ATIVAS
        )

    def obter_tipo(self) -> str:
        return "Cidadão"

# ---------
# EMPRESA
# ---------

class Empresa(Usuario):
    """
    Representa uma empresa no sistema.

    Possui limite mensal de descarte em kg.
    """

    def __init__(self, id, nome, email, cnpj, razao_social) -> None:

        super().__init__(id, nome, email)

        self._validar_cnpj(cnpj)

        self._cnpj: str = cnpj
        self._razao_social: str = razao_social

        self._limite_mensal: float = 1000.0
        self._descartado_mes: float = 0.0

        self._registrar_acao("Empresa criada")

    @staticmethod
    def _validar_cnpj(cnpj: str) -> None:
        padrao = r"^\d{14}$"

        if not re.match(padrao, cnpj):
            raise ValueError("CNPJ deve conter 14 números.")

    def registrar_descarte(self, peso: float) -> None:

        if peso <= 0:
            raise ValueError("Peso inválido.")

        if self._descartado_mes + peso > self._limite_mensal:
            raise Exception("Limite mensal excedido.")

        self._descartado_mes += peso

        self._registrar_acao(f"Descarte registrado: {peso} kg")

    def resetar_mes(self) -> None:
        self._descartado_mes = 0
        self._registrar_acao("Contador mensal resetado")

    def pode_solicitar_descarte(self) -> bool:
        return self.ativo and self._descartado_mes < self._limite_mensal

    def obter_tipo(self) -> str:
        return "Empresa"


# --------------
# ADMINISTRADOR
# --------------


class Administrador(Usuario):
    """
    Representa um administrador do sistema.

    Possui níveis de acesso:

    1 - Básico
    2 - Intermediário
    3 - Total
    """

    def __init__(self, id, nome, email, nivel: int = 1) -> None:

        super().__init__(id, nome, email)

        if nivel not in (1, 2, 3):
            raise ValueError("Nível deve ser 1, 2 ou 3.")

        self._nivel: int = nivel

        self._registrar_acao(f"Administrador nível {nivel} criado")

    @property
    def nivel(self) -> int:
        return self._nivel

    def pode_gerenciar_usuarios(self) -> bool:
        return self._nivel >= 2

    def pode_solicitar_descarte(self) -> bool:
        return False

    def obter_tipo(self) -> str:
        return f"Administrador (Nível {self._nivel})"