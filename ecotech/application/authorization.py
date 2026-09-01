"""Políticas de autorização e escopo operacional do EcoTech."""

from typing import Iterable, List

from ..domain.descarte import SolicitacaoDescarte


def empresa_pode_operar_solicitacao(
    empresa_id: str,
    solicitacao: SolicitacaoDescarte,
    repositorio,
) -> bool:
    """Retorna se a empresa é responsável pela operação da solicitação."""
    empresa_responsavel_id = getattr(solicitacao, "empresa_responsavel_id", None)
    if empresa_responsavel_id is None and hasattr(repositorio, 'buscar_solicitacao'):
        row = repositorio.buscar_solicitacao(solicitacao.id)
        if row and 'empresa_responsavel_id' in row.keys():
            empresa_responsavel_id = row['empresa_responsavel_id']
    if empresa_responsavel_id is not None:
        return empresa_responsavel_id == empresa_id

    ponto = solicitacao.ponto_coleta
    if ponto is None:
        return False

    ponto_row = repositorio.buscar_ponto_coleta(ponto.id)
    return bool(ponto_row and ponto_row["id_empresa"] == empresa_id)


def usuario_pode_visualizar_solicitacao(
    usuario: dict,
    solicitacao: SolicitacaoDescarte,
    repositorio,
) -> bool:
    """Aplica o escopo de leitura de uma solicitação para o usuário logado."""
    if usuario["tipo"] == "administrador":
        return True
    if usuario["tipo"] == "cidadao":
        return solicitacao.usuario.id == usuario["id"]
    if usuario["tipo"] == "empresa":
        return empresa_pode_operar_solicitacao(
            usuario["id"], solicitacao, repositorio
        )
    return False


def usuario_pode_operar_solicitacao(
    usuario: dict,
    solicitacao: SolicitacaoDescarte,
    repositorio,
) -> bool:
    """Autoriza mutações operacionais por administrador ou empresa responsável."""
    if usuario["tipo"] == "administrador":
        return True
    if usuario["tipo"] != "empresa":
        return False
    return empresa_pode_operar_solicitacao(
        usuario["id"], solicitacao, repositorio
    )


def listar_solicitacoes_visiveis_empresa(
    empresa_id: str,
    solicitacoes: Iterable[SolicitacaoDescarte],
    repositorio,
) -> List[SolicitacaoDescarte]:
    """Retorna o escopo operacional único de uma empresa."""
    return [
        solicitacao
        for solicitacao in solicitacoes
        if empresa_pode_operar_solicitacao(
            empresa_id, solicitacao, repositorio
        )
    ]
