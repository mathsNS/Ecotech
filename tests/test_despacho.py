"""Despacho progressivo e persistente de ofertas de coleta."""

import sqlite3
from datetime import datetime, timedelta

from ecotech.application.despacho import ConfiguracaoDespacho, ServicoDespacho
from ecotech.application.elegibilidade import DemandaColeta
from ecotech.application.services import ServicoBaseOperacional
from ecotech.domain.descarte import SolicitacaoDescarte
from ecotech.domain.logistica import Coordenadas
from ecotech.domain.usuarios import Cidadao, Empresa
from ecotech.infrastructure.persistence.dados import Dados


AGORA = datetime(2026, 9, 1, 9, 0)


def _preparar(tmp_path, monkeypatch):
    caminho = str(tmp_path / 'despacho.db')
    original = sqlite3.connect
    monkeypatch.setattr(
        'ecotech.infrastructure.persistence.dados.sqlite3.connect',
        lambda path, **kwargs: original(caminho, **kwargs),
    )
    dados = Dados()
    cidadao = Cidadao('cid-1', 'Nome Privado', 'cid@teste.com', '12345678909')
    dados.salvar_cidadao(cidadao)
    bases = ServicoBaseOperacional(dados)
    cnpjs = ('11222333000181', '14380200000121', '33000167000101')
    for indice, (longitude, cnpj) in enumerate(
        zip((0.01, 0.02, 0.03), cnpjs), 1
    ):
        empresa = Empresa(
            f'emp-{indice}', f'Empresa {indice}', f'e{indice}@teste.com',
            cnpj, f'Empresa {indice} LTDA',
        )
        dados.salvar_empresa(empresa)
        bases.criar(empresa.id, {
            'id': f'base-{indice}', 'nome': f'Base {indice}',
            'endereco': f'Rua Base {indice}', 'latitude': 0,
            'longitude': longitude, 'raio_atendimento_km': 50,
            'capacidade_kg': 100, 'realiza_coleta_domiciliar': True,
        })
    solicitacao = SolicitacaoDescarte('sol-1', cidadao)
    dados.salvar_solicitacao(solicitacao)
    dados.atualizar_detalhes_coleta(
        solicitacao.id, 'domiciliar', 'Rua Secreta, 123', 'Contato Privado',
        '2026-09-01 10:00',
    )
    demanda = DemandaColeta(
        Coordenadas(0, 0), frozenset({'celular'}), 5,
        datetime(2026, 9, 1, 10),
    )
    servico = ServicoDespacho(
        dados, bases,
        configuracao=ConfiguracaoDespacho((1, 2), 5),
    )
    return dados, servico, demanda


def test_primeiro_lote_ativa_e_demais_aguardam(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch)
    servico.criar_ofertas('sol-1', demanda, AGORA)

    ofertas = dados.buscar_ofertas_solicitacao('sol-1')
    assert [o['status'] for o in ofertas] == ['ATIVA', 'AGUARDANDO', 'AGUARDANDO']
    assert [o['rodada'] for o in ofertas] == [1, 2, 2]
    assert dados.buscar_solicitacao('sol-1')['estado'] == 'BUSCANDO_EMPRESA'
    assert len(dados.buscar_notificacoes_usuario('emp-1')) == 1
    assert dados.buscar_notificacoes_usuario('emp-2') == []


def test_notificacao_pre_aceite_nao_expoe_dados_pessoais(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch)
    servico.criar_ofertas('sol-1', demanda, AGORA)
    mensagem = dados.buscar_notificacoes_usuario('emp-1')[0]['mensagem']
    assert 'Nome Privado' not in mensagem
    assert 'Rua Secreta' not in mensagem
    assert 'Contato Privado' not in mensagem
    assert 'celular' in mensagem
    assert '5 kg' in mensagem


def test_expiracao_ativa_proximo_lote_sem_duplicar_notificacoes(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch)
    servico.criar_ofertas('sol-1', demanda, AGORA)
    depois = AGORA + timedelta(minutes=6)
    ativadas = servico.processar_ofertas_expiradas(depois)
    repetida = servico.processar_ofertas_expiradas(depois)

    ofertas = dados.buscar_ofertas_solicitacao('sol-1')
    assert [o['status'] for o in ofertas] == ['EXPIRADA', 'ATIVA', 'ATIVA']
    assert len(ativadas) == 2
    assert repetida == []
    assert len(dados.buscar_notificacoes_usuario('emp-2')) == 1
    assert len(dados.buscar_notificacoes_usuario('emp-3')) == 1


def test_esgotamento_mantem_solicitacao_recuperavel(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch)
    servico.criar_ofertas('sol-1', demanda, AGORA)
    servico.processar_ofertas_expiradas(AGORA + timedelta(minutes=6))
    servico.processar_ofertas_expiradas(AGORA + timedelta(minutes=12))

    solicitacao = dados.buscar_solicitacao('sol-1')
    assert solicitacao['estado'] == 'BUSCANDO_EMPRESA'
    assert solicitacao['despacho_esgotado_em'] is not None
    assert all(
        o['status'] == 'EXPIRADA'
        for o in dados.buscar_ofertas_solicitacao('sol-1')
    )


def test_base_nao_elegivel_nao_recebe_oferta(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch)
    dados.definir_atividade_base('base-1', 'emp-1', False)
    servico.criar_ofertas('sol-1', demanda, AGORA)
    bases_ofertadas = {
        o['base_operacional_id'] for o in dados.buscar_ofertas_solicitacao('sol-1')
    }
    assert 'base-1' not in bases_ofertadas
    assert dados.buscar_notificacoes_usuario('emp-1') == []
