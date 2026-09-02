"""Migration 011: fotos opcionais dos produtos descartados."""


def aplicar(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS solicitacao_foto (
        id TEXT PRIMARY KEY,
        solicitacao_id TEXT NOT NULL,
        nome_arquivo TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        tamanho INTEGER NOT NULL,
        conteudo BLOB NOT NULL,
        criada_em TEXT NOT NULL,
        FOREIGN KEY(solicitacao_id) REFERENCES solicitacao_descarte(id)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_foto_solicitacao ON solicitacao_foto(solicitacao_id, criada_em)")
