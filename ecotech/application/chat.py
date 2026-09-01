"""Casos de uso do chat privado da coleta."""
import json, uuid
from datetime import datetime

TIPOS_EVENTO={'SISTEMA','PROPOSTA_HORARIO','HORARIO_ACEITO','HORARIO_RECUSADO','COLETA_CONFIRMADA'}

class ServicoChat:
    def __init__(self,dados): self._dados=dados
    def criar_para_atribuicao(self,solicitacao_id,agora=None):
        return self._dados.criar_conversa_solicitacao(solicitacao_id,(agora or datetime.now()).isoformat())
    def enviar(self,solicitacao_id,usuario_id,texto,agora=None):
        texto=(texto or '').strip()
        if not texto or len(texto)>2000: raise ValueError('mensagem deve possuir entre 1 e 2000 caracteres')
        return self._dados.salvar_mensagem_chat(str(uuid.uuid4()),solicitacao_id,usuario_id,'MENSAGEM',texto,'{}',(agora or datetime.now()).isoformat())
    def evento(self,solicitacao_id,tipo,payload,agora=None):
        if tipo not in TIPOS_EVENTO: raise ValueError('tipo de evento inválido')
        return self._dados.salvar_mensagem_chat(str(uuid.uuid4()),solicitacao_id,None,tipo,None,json.dumps(payload,sort_keys=True),(agora or datetime.now()).isoformat(),sistema=True)
    def listar(self,solicitacao_id,usuario_id,pagina=1,limite=50):
        return self._dados.buscar_mensagens_chat(solicitacao_id,usuario_id,max(1,pagina),min(max(1,limite),100))
    def marcar_lidas(self,solicitacao_id,usuario_id,agora=None):
        return self._dados.marcar_mensagens_chat_lidas(solicitacao_id,usuario_id,(agora or datetime.now()).isoformat())
    def encerrar(self,solicitacao_id,usuario_id,agora=None):
        return self._dados.encerrar_conversa_solicitacao(solicitacao_id,usuario_id,(agora or datetime.now()).isoformat())
