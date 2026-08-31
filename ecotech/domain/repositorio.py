"""Interfaces abstratas de repositório."""

from abc import ABC, abstractmethod
from typing import List, Optional, Any


class RepositorioBase(ABC):
    """Contrato base de persistência. Implementações concretas herdam desta classe."""

    # --- Usuários: salvar ---

    @abstractmethod
    def salvar_cidadao(self, cidadao: Any, password_hash: str = "") -> None:
        """Persiste um cidadão no repositório."""
        ...

    @abstractmethod
    def salvar_empresa(self, empresa: Any, password_hash: str = "") -> None:
        """Persiste uma empresa no repositório."""
        ...

    @abstractmethod
    def salvar_administrador(self, administrador: Any, password_hash: str = "") -> None:
        """Persiste um administrador no repositório."""
        ...

    # --- Usuários: buscar ---

    @abstractmethod
    def buscar_usuario(self, id_usuario: str) -> Optional[Any]:
        """Busca um usuário pelo ID."""
        ...

    @abstractmethod
    def buscar_usuario_por_cpf(self, cpf: str) -> Optional[Any]:
        """Busca um cidadão pelo CPF. Retorna linha com password_hash."""
        ...

    @abstractmethod
    def buscar_usuario_por_cnpj(self, cnpj: str) -> Optional[Any]:
        """Busca uma empresa pelo CNPJ. Retorna linha com password_hash."""
        ...

    @abstractmethod
    def buscar_usuario_por_email(self, email: str) -> Optional[Any]:
        """Busca um usuário pelo e-mail. Retorna linha com password_hash."""
        ...

    @abstractmethod
    def buscar_todos_usuarios(self) -> List[Any]:
        """Retorna todos os usuários cadastrados."""
        ...

    @abstractmethod
    def buscar_cidadao(self, id_usuario: str) -> Optional[Any]:
        """Busca dados de cidadão (com CPF e pontos) pelo ID do usuário."""
        ...

    @abstractmethod
    def buscar_empresa(self, id_usuario: str) -> Optional[Any]:
        """Busca dados de empresa (com CNPJ e razão social) pelo ID do usuário."""
        ...

    # --- Usuários: atualizar / desativar ---

    @abstractmethod
    def desativar_usuario(self, id_usuario: str) -> None:
        """Desativa (soft-delete) um usuário pelo ID."""
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
    def buscar_ponto_coleta(self, id_ponto: str) -> Optional[Any]:
        """Busca um ponto de coleta pelo ID."""
        ...

    @abstractmethod
    def buscar_todos_pontos_coleta(self) -> List[Any]:
        """Retorna todos os pontos de coleta ativos."""
        ...

    @abstractmethod
    def atualizar_ocupacao_ponto(self, id_ponto: str, ocupacao_atual_kg: float) -> None:
        """Atualiza a ocupação atual de um ponto de coleta."""
        ...

    @abstractmethod
    def salvar_base_operacional(self, base: Any) -> None: ...

    @abstractmethod
    def buscar_base_operacional(self, id_base: str) -> Optional[Any]: ...

    @abstractmethod
    def buscar_bases_empresa(self, id_empresa: str) -> List[Any]: ...

    @abstractmethod
    def atualizar_base_operacional(self, base: Any) -> None: ...

    @abstractmethod
    def definir_atividade_base(
        self, id_base: str, id_empresa: str, ativa: bool
    ) -> None: ...

    # --- Solicitações: salvar ---

    @abstractmethod
    def salvar_solicitacao(self, solicitacao: Any) -> None:
        """Persiste uma solicitação de descarte no repositório."""
        ...

    @abstractmethod
    def salvar_itens_descarte(self, id_solicitacao: str, item: Any) -> None:
        """Persiste um item de descarte vinculado a uma solicitação."""
        ...

    @abstractmethod
    def salvar_historico_rastreamento(self, id_solicitacao: str, mensagem: str) -> None:
        """Persiste uma entrada no histórico de rastreamento de uma solicitação."""
        ...

    # --- Solicitações: buscar ---

    @abstractmethod
    def buscar_solicitacao(self, id_solicitacao: str) -> Optional[Any]:
        """Busca uma solicitação de descarte pelo ID."""
        ...

    @abstractmethod
    def buscar_todas_solicitacoes(self) -> List[Any]:
        """Retorna todas as solicitações de descarte."""
        ...

    @abstractmethod
    def buscar_solicitacoes_usuario(self, id_usuario: str) -> List[Any]:
        """Retorna todas as solicitações de um usuário específico."""
        ...

    @abstractmethod
    def buscar_itens_solicitacao(self, id_solicitacao: str) -> List[Any]:
        """Retorna todos os itens de uma solicitação específica."""
        ...

    # --- Solicitações: atualizar ---

    @abstractmethod
    def atualizar_solicitacao(self, id_solicitacao: str, estado: str,
                               metodo_tratamento: Optional[str] = None) -> None:
        """Atualiza o estado (e opcionalmente o método de tratamento) de uma solicitação."""
        ...

    @abstractmethod
    def atualizar_localizacao_coleta(
        self, id_solicitacao: str, latitude: float, longitude: float,
        origem: str
    ) -> None: ...

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

    @abstractmethod
    def salvar_saque(self, id_saque: str, id_usuario: str, valor: float,
                     metodo: str, data: str, hora: str, status: str) -> None:
        """Persiste uma solicitação de saque."""
        ...

    @abstractmethod
    def buscar_saques_usuario(self, id_usuario: str) -> List[Any]:
        """Retorna todos os saques de um usuário."""
        ...

    @abstractmethod
    def buscar_total_sacado_usuario(self, id_usuario: str) -> float:
        """Retorna o total já sacado (pendente ou finalizado) por um usuário."""
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

    @abstractmethod
    def buscar_todos_cidadaos_admin(self) -> List[Any]:
        """Retorna dados completos de todos os cidadãos para visão administrativa."""
        ...

    @abstractmethod
    def buscar_todos_empresas_admin(self) -> List[Any]:
        """Retorna dados completos de todas as empresas para visão administrativa."""
        ...
