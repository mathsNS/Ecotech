"""Cenário integrado da coleta domiciliar com relógio controlado."""
from datetime import datetime, timedelta
import json, pytest
from ecotech.application.agendamento import ServicoAgendamento
from ecotech.application.chat import ServicoChat
from tests.test_despacho import _preparar, AGORA

def test_fluxo_domiciliar_completo_sem_espera_real(tmp_path,monkeypatch):
    dados,despacho,demanda=_preparar(tmp_path,monkeypatch)
    agenda=ServicoAgendamento(dados); chat=ServicoChat(dados)
    inicio=AGORA+timedelta(days=2); fim=inicio+timedelta(hours=2)
    agenda.solicitar('sol-1','cid-1',inicio,fim,AGORA)

    despacho.criar_ofertas('sol-1',demanda,AGORA)
    ofertas=dados.buscar_ofertas_solicitacao('sol-1')
    assert [o['status'] for o in ofertas]==['ATIVA','AGUARDANDO','AGUARDANDO']
    assert 'Rua Secreta' not in ofertas[0]['snapshot_fatores']

    despacho.processar_ofertas_expiradas(AGORA+timedelta(minutes=6))
    ofertas=dados.buscar_ofertas_solicitacao('sol-1')
    assert [o['status'] for o in ofertas]==['EXPIRADA','ATIVA','ATIVA']
    vencedora=ofertas[1]
    despacho.aceitar(vencedora['id'],vencedora['empresa_id'],AGORA+timedelta(minutes=7))
    with pytest.raises(RuntimeError):
        despacho.aceitar(ofertas[2]['id'],ofertas[2]['empresa_id'],AGORA+timedelta(minutes=7))
    assert dados.buscar_solicitacao('sol-1')['empresa_responsavel_id']==vencedora['empresa_id']

    chat.enviar('sol-1','cid-1','Podemos ajustar o horário?',AGORA)
    mensagens = chat.listar('sol-1', vencedora['empresa_id'])
    assert mensagens[0]['remetente_nome'] == 'Nome Privado'
    assert dados.contar_notificacoes_nao_lidas(vencedora['empresa_id']) >= 1
    novo=inicio+timedelta(hours=1)
    agenda.propor('sol-1',vencedora['empresa_id'],novo,novo+timedelta(hours=2),AGORA)
    chat.evento('sol-1','PROPOSTA_HORARIO',{'inicio':novo.isoformat()},AGORA)
    confirmado=agenda.aceitar('sol-1','cid-1',AGORA)
    assert confirmado['status']=='AGENDADO'
    assert confirmado['inicio_confirmado']==novo.isoformat()
    assert len(chat.listar('sol-1','cid-1'))==2

    tipos={r['tipo'] for r in dados.conn.execute('SELECT tipo FROM evento_operacional')}
    assert {'OFERTAS_CRIADAS','RODADA_ATIVADA','OFERTA_ACEITA','CONFLITO_ACEITE','AGENDAMENTO_CONFIRMADO'} <= tipos
    diagnostico = dados.buscar_diagnostico_despacho()
    assert diagnostico['metricas']['aceitas'] == 1
    assert diagnostico['eventos']['conflitos'] == 1
    assert diagnostico['tempo_agendamento']['minutos_atribuicao_ate_agendamento'] is not None
    assert diagnostico['destinatarios'][0]['empresa_nome']
