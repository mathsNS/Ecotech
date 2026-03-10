"""
Módulo de interfaces de repositório.

Define contratos abstratos para persistência de dados, permitindo
que as camadas de aplicação dependam de abstrações ao invés de
implementações concretas (Dependency Inversion Principle).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any


class RepositorioBase(ABC):
    """
    Interface abstrata que define o contrato de persistência do sistema.

    Todas as implementações concretas de armazenamento (SQLite, PostgreSQL,
    em memória, etc.) devem herdar desta classe e implementar seus métodos.
    Isso garante que a camada de aplicação não dependa de detalhes de
    infraestrutura.
    """

    # --- Usuários ---

    @abstractmethod
    def salvar_cidadao(self, cidadao: Any) -> None:
        """Persiste um cidadão no repositório."""
        ...

    @abstractmethod
    def salvar_empresa(self, empresa: Any) -> None:
        """Persiste uma empresa no repositório."""
        ...

    @abstractmethod
    def salvar_administrador(self, administrador: Any) -> None:
        """Persiste um administrador no repositório."""
        ...

    @abstractmethod
    def buscar_todos_usuarios(self) -> List[Any]:
        """Retorna todos os usuários cadastrados."""
        ...

    @abstractmethod
    def buscar_cidadao(self, id_usuario: str) -> Optional[Any]:
        """Busca dados de cidadão pelo ID do usuário."""
        ...

    @abstractmethod
    def buscar_empresa(self, id_usuario: str) -> Optional[Any]:
        """Busca dados de empresa pelo ID do usuário."""
        ...

    # --- Dispositivos ---

    @abstractmethod
    def salvar_dispositivo(self, dispositivo: Any) -> None:
        """Persiste um dispositivo no repositório."""
        ...

    @abstractmethod
    def buscar_dispositivo(self, id_dispositivo: str) -> Optional[Any]:
        """Busca um dispositivo pelo ID."""
        ...

    # --- Pontos de Coleta ---

    @abstractmethod
    def salvar_ponto(self, ponto_coleta: Any) -> None:
        """Persiste um ponto de coleta no repositório."""
        ...

    @abstractmethod
    def buscar_todos_pontos_coleta(self) -> List[Any]:
        """Retorna todos os pontos de coleta ativos."""
        ...

    # --- Solicitações ---

    @abstractmethod
    def salvar_solicitacao(self, solicitacao: Any) -> None:
        """Persiste uma solicitação de descarte no repositório."""
        ...

    @abstractmethod
    def salvar_itens_descarte(self, id_solicitacao: str, item: Any) -> None:
        """Persiste um item de descarte vinculado a uma solicitação."""
        ...

    @abstractmethod
    def buscar_todas_solicitacoes(self) -> List[Any]:
        """Retorna todas as solicitações de descarte."""
        ...

    @abstractmethod
    def buscar_itens_solicitacao(self, id_solicitacao: str) -> List[Any]:
        """Retorna todos os itens de uma solicitação específica."""
        ...

    # --- Notificações e Entregas ---

    @abstractmethod
    def salvar_notificacao(self, id_usuario: str, mensagem: str) -> None:
        """Persiste uma notificação para um usuário."""
        ...

    @abstractmethod
    def buscar_notificacoes_usuario(self, id_usuario: str) -> List[Any]:
        """Retorna todas as notificações de um usuário."""
        ...

    @abstractmethod
    def salvar_entrega(self, id_entrega: str, id_usuario: str, valor: float,
                       empresa: str, data: str, hora: str, status: str) -> None:
        """Persiste uma entrega/transação."""
        ...

    @abstractmethod
    def buscar_entregas_usuario(self, id_usuario: str) -> List[Any]:
        """Retorna todas as entregas de um usuário."""
        ...

    # --- Contagens ---

    @abstractmethod
    def contar_usuarios(self) -> int:
        """Retorna o total de usuários cadastrados."""
        ...

    @abstractmethod
    def contar_solicitacoes(self) -> int:
        """Retorna o total de solicitações registradas."""
        ...
