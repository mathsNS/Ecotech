from datetime import timedelta
import json, pytest
from ecotech.application.chat import ServicoChat
from ecotech.application.despacho import ServicoDespacho
from ecotech.infrastructure.persistence.dados import Dados
from tests.test_despacho import _preparar, AGORA

def preparar(tmp_path,monkeypatch):
    dados,despacho,demanda=_preparar(tmp_path,monkeypatch)
    chat=ServicoChat(dados)
    with pytest.raises(ValueError): chat.criar_para_atribuicao('sol-1',AGORA)
    despacho.criar_ofertas('sol-1',demanda,AGORA)
    oferta=dados.buscar_ofertas_solicitacao('sol-1')[0]
    despacho.aceitar(oferta['id'],'emp-1',AGORA+timedelta(minutes=1))
    return dados,chat

def test_conversa_criada_uma_vez_apos_aceite(tmp_path,monkeypatch):
    dados,chat=preparar(tmp_path,monkeypatch)
    primeira=chat.criar_para_atribuicao('sol-1',AGORA)
    segunda=chat.criar_para_atribuicao('sol-1',AGORA)
    assert primeira['id']==segunda['id']
    assert dados.conn.execute('SELECT COUNT(*) FROM conversa_solicitacao').fetchone()[0]==1

def test_participantes_enviam_e_terceiros_nao_acessam(tmp_path,monkeypatch):
    _,chat=preparar(tmp_path,monkeypatch)
    chat.enviar('sol-1','cid-1','Olá',AGORA)
    chat.enviar('sol-1','emp-1','Confirmado',AGORA)
    assert len(chat.listar('sol-1','cid-1'))==2
    assert len(chat.listar('sol-1','emp-1'))==2
    with pytest.raises(PermissionError): chat.listar('sol-1','emp-2')

def test_mensagem_vazia_evento_formal_e_leitura(tmp_path,monkeypatch):
    _,chat=preparar(tmp_path,monkeypatch)
    with pytest.raises(ValueError): chat.enviar('sol-1','cid-1','   ',AGORA)
    evento=chat.evento('sol-1','PROPOSTA_HORARIO',{'inicio':'2026-09-03T10:00:00'},AGORA)
    assert json.loads(evento['payload'])['inicio']=='2026-09-03T10:00:00'
    assert chat.marcar_lidas('sol-1','emp-1',AGORA)==1

def test_encerramento_preserva_historico_e_bloqueia_envio(tmp_path,monkeypatch):
    _,chat=preparar(tmp_path,monkeypatch)
    chat.enviar('sol-1','cid-1','Antes de encerrar',AGORA)
    chat.encerrar('sol-1','emp-1',AGORA)
    assert len(chat.listar('sol-1','cid-1'))==1
    with pytest.raises(ValueError): chat.enviar('sol-1','cid-1','Depois',AGORA)
