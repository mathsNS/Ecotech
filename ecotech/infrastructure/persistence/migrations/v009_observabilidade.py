"""Migration 009: eventos operacionais estruturados."""

def aplicar(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS evento_operacional (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL,
        solicitacao_id TEXT, oferta_id TEXT, detalhes TEXT NOT NULL DEFAULT '{}',
        criado_em TEXT NOT NULL,
        FOREIGN KEY(solicitacao_id) REFERENCES solicitacao_descarte(id),
        FOREIGN KEY(oferta_id) REFERENCES oferta_coleta(id)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_evento_tipo_data ON evento_operacional(tipo,criado_em)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_evento_solicitacao ON evento_operacional(solicitacao_id,criado_em)")
