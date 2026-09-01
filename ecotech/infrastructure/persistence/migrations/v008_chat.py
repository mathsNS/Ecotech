"""Migration 008: conversa segura por solicitação atribuída."""

def aplicar(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS conversa_solicitacao (
        id TEXT PRIMARY KEY, solicitacao_id TEXT NOT NULL UNIQUE,
        cidadao_id TEXT NOT NULL, empresa_id TEXT NOT NULL,
        criada_em TEXT NOT NULL, encerrada_em TEXT,
        FOREIGN KEY(solicitacao_id) REFERENCES solicitacao_descarte(id),
        FOREIGN KEY(cidadao_id) REFERENCES usuario(id), FOREIGN KEY(empresa_id) REFERENCES usuario(id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS mensagem_chat (
        id TEXT PRIMARY KEY, conversa_id TEXT NOT NULL, remetente_id TEXT,
        tipo TEXT NOT NULL CHECK(tipo IN ('MENSAGEM','SISTEMA','PROPOSTA_HORARIO','HORARIO_ACEITO','HORARIO_RECUSADO','COLETA_CONFIRMADA')),
        texto TEXT, payload TEXT NOT NULL DEFAULT '{}', criado_em TEXT NOT NULL, lida_em TEXT,
        FOREIGN KEY(conversa_id) REFERENCES conversa_solicitacao(id)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mensagem_conversa_data ON mensagem_chat(conversa_id,criado_em,id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mensagem_leitura ON mensagem_chat(conversa_id,lida_em)")
