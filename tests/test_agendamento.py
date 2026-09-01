from datetime import datetime, timedelta
import pytest
from ecotech.application.agendamento import ServicoAgendamento
from tests.test_despacho import _preparar, AGORA

def preparar(tmp_path, monkeypatch):
    dados, despacho, demanda = _preparar(tmp_path, monkeypatch)
    despacho.criar_ofertas('sol-1', demanda, AGORA)
    oferta=dados.buscar_ofertas_solicitacao('sol-1')[0]
    despacho.aceitar(oferta['id'],'emp-1',AGORA+timedelta(minutes=1))
    agenda=ServicoAgendamento(dados)
    inicio=AGORA+timedelta(days=2); fim=inicio+timedelta(hours=2)
    agenda.solicitar('sol-1','cid-1',inicio,fim,AGORA)
    return dados,agenda,inicio,fim

def test_janela_invalida_e_rejeitada(tmp_path,monkeypatch):
    _,agenda,inicio,_=preparar(tmp_path,monkeypatch)
    with pytest.raises(ValueError): agenda.propor('sol-1','emp-1',inicio,inicio,AGORA)

def test_empresa_aceita_janela_inicial_e_idempotente(tmp_path,monkeypatch):
    dados,agenda,inicio,fim=preparar(tmp_path,monkeypatch)
    assert agenda.aceitar('sol-1','emp-1',AGORA)['status']=='AGENDADO'
    agenda.aceitar('sol-1','emp-1',AGORA)
    row=dados.buscar_agendamento('sol-1')
    assert row['inicio_confirmado']==inicio.isoformat()
    assert row['versao']==2

def test_proposta_nao_altera_final_ate_consenso(tmp_path,monkeypatch):
    dados,agenda,inicio,_=preparar(tmp_path,monkeypatch)
    novo=inicio+timedelta(hours=3)
    row=agenda.propor('sol-1','emp-1',novo,novo+timedelta(hours=1),AGORA)
    assert row['status']=='PROPOSTA_PENDENTE' and row['inicio_confirmado'] is None
    with pytest.raises(PermissionError): agenda.aceitar('sol-1','emp-1',AGORA)
    assert agenda.aceitar('sol-1','cid-1',AGORA)['status']=='AGENDADO'

def test_cidadao_rejeita_e_outra_empresa_nao_acessa(tmp_path,monkeypatch):
    _,agenda,inicio,_=preparar(tmp_path,monkeypatch)
    agenda.propor('sol-1','emp-1',inicio+timedelta(hours=3),inicio+timedelta(hours=4),AGORA)
    assert agenda.rejeitar('sol-1','cid-1',AGORA)['status']=='AGUARDANDO_AGENDAMENTO'
    with pytest.raises(PermissionError): agenda.propor('sol-1','emp-2',inicio,inicio+timedelta(hours=1),AGORA)
