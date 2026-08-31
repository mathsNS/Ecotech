"""Testes das políticas centrais de autorização por propriedade."""

from ecotech.application.authorization import (
    empresa_pode_operar_solicitacao,
    listar_solicitacoes_visiveis_empresa,
    usuario_pode_operar_solicitacao,
    usuario_pode_visualizar_solicitacao,
)
from ecotech.domain.descarte import PontoColeta, SolicitacaoDescarte
from ecotech.domain.usuarios import Cidadao


class RepositorioPontosFake:
    def __init__(self, proprietarios):
        self.proprietarios = proprietarios

    def buscar_ponto_coleta(self, id_ponto):
        empresa_id = self.proprietarios.get(id_ponto)
        return {'id': id_ponto, 'id_empresa': empresa_id} if empresa_id else None


def criar_solicitacao(id_sol, ponto=None):
    cidadao = Cidadao('cid-1', 'Cidadão Teste', 'cidadao@teste.com', '12345678909')
    return SolicitacaoDescarte(id_sol, cidadao, ponto)


def test_empresa_proprietaria_pode_operar():
    ponto = PontoColeta('ponto-a', 'Ponto A', 'Rua A', -7.2, -39.3)
    solicitacao = criar_solicitacao('sol-1', ponto)
    repositorio = RepositorioPontosFake({'ponto-a': 'empresa-a'})

    assert empresa_pode_operar_solicitacao('empresa-a', solicitacao, repositorio)


def test_outra_empresa_nao_pode_operar():
    ponto = PontoColeta('ponto-a', 'Ponto A', 'Rua A', -7.2, -39.3)
    solicitacao = criar_solicitacao('sol-1', ponto)
    repositorio = RepositorioPontosFake({'ponto-a': 'empresa-a'})

    assert not empresa_pode_operar_solicitacao('empresa-b', solicitacao, repositorio)


def test_coleta_domiciliar_sem_atribuicao_nao_pode_ser_operada_por_empresa():
    solicitacao = criar_solicitacao('sol-domiciliar')
    repositorio = RepositorioPontosFake({})

    assert not empresa_pode_operar_solicitacao('empresa-a', solicitacao, repositorio)


def test_admin_pode_operar_qualquer_solicitacao():
    solicitacao = criar_solicitacao('sol-1')
    repositorio = RepositorioPontosFake({})
    admin = {'id': 'admin-1', 'tipo': 'administrador'}

    assert usuario_pode_operar_solicitacao(admin, solicitacao, repositorio)


def test_cidadao_visualiza_apenas_solicitacao_propria():
    solicitacao = criar_solicitacao('sol-1')
    repositorio = RepositorioPontosFake({})

    assert usuario_pode_visualizar_solicitacao(
        {'id': 'cid-1', 'tipo': 'cidadao'}, solicitacao, repositorio
    )
    assert not usuario_pode_visualizar_solicitacao(
        {'id': 'cid-2', 'tipo': 'cidadao'}, solicitacao, repositorio
    )


def test_listagem_empresa_usa_propriedade_do_ponto():
    ponto_a = PontoColeta('ponto-a', 'Ponto A', 'Rua A', -7.2, -39.3)
    ponto_b = PontoColeta('ponto-b', 'Ponto B', 'Rua B', -7.3, -39.4)
    solicitacao_a = criar_solicitacao('sol-a', ponto_a)
    solicitacao_b = criar_solicitacao('sol-b', ponto_b)
    repositorio = RepositorioPontosFake({
        'ponto-a': 'empresa-a',
        'ponto-b': 'empresa-b',
    })

    assert listar_solicitacoes_visiveis_empresa(
        'empresa-a', [solicitacao_a, solicitacao_b], repositorio
    ) == [solicitacao_a]
