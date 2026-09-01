"""Migration 007: negociação formal de janelas de coleta."""

def aplicar(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS agendamento_coleta (
        solicitacao_id TEXT PRIMARY KEY, janela_inicio TEXT NOT NULL, janela_fim TEXT NOT NULL,
        proposta_inicio TEXT, proposta_fim TEXT, proposta_por TEXT,
        inicio_confirmado TEXT, fim_confirmado TEXT,
        status TEXT NOT NULL CHECK(status IN ('AGUARDANDO_AGENDAMENTO','JANELA_ACEITA','PROPOSTA_PENDENTE','AGENDADO')),
        versao INTEGER NOT NULL DEFAULT 1, atualizado_em TEXT NOT NULL,
        FOREIGN KEY(solicitacao_id) REFERENCES solicitacao_descarte(id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS historico_agendamento (
        id INTEGER PRIMARY KEY AUTOINCREMENT, solicitacao_id TEXT NOT NULL,
        autor_id TEXT NOT NULL, acao TEXT NOT NULL, inicio TEXT, fim TEXT, criado_em TEXT NOT NULL,
        FOREIGN KEY(solicitacao_id) REFERENCES solicitacao_descarte(id)
    )""")
