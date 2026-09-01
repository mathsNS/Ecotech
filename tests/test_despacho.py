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


def _preparar(tmp_path, monkeypatch, lotes=(1, 2)):
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
        configuracao=ConfiguracaoDespacho(lotes, 5),
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


def test_recusa_ativa_proximo_lote_e_e_idempotente(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch)
    servico.criar_ofertas('sol-1', demanda, AGORA)
    primeira = dados.buscar_ofertas_solicitacao('sol-1')[0]
    servico.recusar(primeira['id'], 'emp-1', 'Sem veículo', AGORA)
    servico.recusar(primeira['id'], 'emp-1', 'repetida', AGORA)
    assert [o['status'] for o in dados.buscar_ofertas_solicitacao('sol-1')] == [
        'RECUSADA', 'ATIVA', 'ATIVA'
    ]


def test_aceite_ativo_atribui_e_cancela_concorrentes(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch, (2, 1))
    servico.criar_ofertas('sol-1', demanda, AGORA)
    oferta = dados.buscar_ofertas_solicitacao('sol-1')[0]
    aceita = servico.aceitar(oferta['id'], oferta['empresa_id'], AGORA + timedelta(minutes=1))
    solicitacao = dados.buscar_solicitacao('sol-1')
    assert aceita['endereco_coleta'] == 'Rua Secreta, 123'
    assert solicitacao['empresa_responsavel_id'] == oferta['empresa_id']
    assert solicitacao['base_operacional_id'] == oferta['base_operacional_id']
    assert [o['status'] for o in dados.buscar_ofertas_solicitacao('sol-1')] == [
        'ACEITA', 'CANCELADA', 'CANCELADA'
    ]
    assert len(dados.buscar_notificacoes_usuario('cid-1')) == 1


def test_repetir_aceite_vencedor_e_idempotente(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch)
    servico.criar_ofertas('sol-1', demanda, AGORA)
    oferta = dados.buscar_ofertas_solicitacao('sol-1')[0]
    servico.aceitar(oferta['id'], 'emp-1', AGORA + timedelta(minutes=1))
    servico.aceitar(oferta['id'], 'emp-1', AGORA + timedelta(minutes=2))
    assert dados.buscar_solicitacao('sol-1')['versao_atribuicao'] == 1
    assert len(dados.buscar_notificacoes_usuario('cid-1')) == 1


def test_oferta_expirada_e_empresa_sem_oferta_nao_aceitam(tmp_path, monkeypatch):
    dados, servico, demanda = _preparar(tmp_path, monkeypatch)
    servico.criar_ofertas('sol-1', demanda, AGORA)
    oferta = dados.buscar_ofertas_solicitacao('sol-1')[0]
    import pytest
    with pytest.raises(TimeoutError):
        servico.aceitar(oferta['id'], 'emp-1', AGORA + timedelta(minutes=6))
    with pytest.raises(LookupError):
        servico.aceitar(oferta['id'], 'emp-2', AGORA + timedelta(minutes=1))


def test_aceites_concorrentes_produzem_um_unico_vencedor(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    dados, servico, demanda = _preparar(tmp_path, monkeypatch, (2, 1))
    servico.criar_ofertas('sol-1', demanda, AGORA)
    ofertas = dados.buscar_ofertas_solicitacao('sol-1')[:2]
    repositorios = [Dados(), Dados()]

    def aceitar(indice):
        oferta = ofertas[indice]
        try:
            ServicoDespacho(repositorios[indice]).aceitar(
                oferta['id'], oferta['empresa_id'], AGORA + timedelta(minutes=1)
            )
            return 'aceita'
        except RuntimeError:
            return 'conflito'

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(aceitar, (0, 1)))
    assert sorted(resultados) == ['aceita', 'conflito']
    assert dados.conn.execute(
        "SELECT COUNT(*) FROM oferta_coleta WHERE status = 'ACEITA'"
    ).fetchone()[0] == 1
