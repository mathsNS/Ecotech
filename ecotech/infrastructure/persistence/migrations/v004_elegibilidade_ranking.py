"""Migration 004: critérios operacionais para elegibilidade de bases."""


def _coluna_existe(conn, tabela, coluna) -> bool:
    return any(row[1] == coluna for row in conn.execute(f"PRAGMA table_info({tabela})"))


def aplicar(conn) -> None:
    if not _coluna_existe(conn, 'base_operacional', 'indisponivel_ate'):
        conn.execute("ALTER TABLE base_operacional ADD COLUMN indisponivel_ate TEXT")
    if not _coluna_existe(conn, 'solicitacao_descarte', 'base_operacional_id'):
        conn.execute("ALTER TABLE solicitacao_descarte ADD COLUMN base_operacional_id TEXT")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS base_categoria (
            base_id TEXT NOT NULL, categoria TEXT NOT NULL COLLATE NOCASE,
            PRIMARY KEY(base_id, categoria),
            FOREIGN KEY(base_id) REFERENCES base_operacional(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS base_disponibilidade (
            base_id TEXT NOT NULL,
            dia_semana INTEGER NOT NULL CHECK(dia_semana BETWEEN 0 AND 6),
            hora_inicio TEXT NOT NULL, hora_fim TEXT NOT NULL,
            CHECK(hora_inicio < hora_fim),
            PRIMARY KEY(base_id, dia_semana, hora_inicio, hora_fim),
            FOREIGN KEY(base_id) REFERENCES base_operacional(id) ON DELETE CASCADE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_base_categoria_categoria ON base_categoria(categoria, base_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_solicitacao_base_estado ON solicitacao_descarte(base_operacional_id, estado)")
    conn.execute("INSERT OR IGNORE INTO base_categoria(base_id, categoria) SELECT id, '*' FROM base_operacional")
