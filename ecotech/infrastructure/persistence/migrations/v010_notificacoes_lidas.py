"""Migration 010: controle de leitura das notificações."""


def aplicar(conn):
    colunas = {
        row[1] for row in conn.execute("PRAGMA table_info(notificacao)").fetchall()
    }
    if "lida_em" not in colunas:
        conn.execute("ALTER TABLE notificacao ADD COLUMN lida_em TEXT")
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notificacao_usuario_leitura
        ON notificacao(id_usuario, lida_em)
    """)
