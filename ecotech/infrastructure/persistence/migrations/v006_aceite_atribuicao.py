"""Migration 006: atribuição atômica da coleta a uma única empresa."""


def _coluna_existe(conn, tabela, coluna):
    return any(row[1] == coluna for row in conn.execute(f"PRAGMA table_info({tabela})"))


def aplicar(conn) -> None:
    for coluna, definicao in (
        ('empresa_responsavel_id', 'TEXT'),
        ('atribuida_em', 'TEXT'),
        ('versao_atribuicao', 'INTEGER NOT NULL DEFAULT 0'),
    ):
        if not _coluna_existe(conn, 'solicitacao_descarte', coluna):
            conn.execute(f"ALTER TABLE solicitacao_descarte ADD COLUMN {coluna} {definicao}")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_solicitacao_empresa_responsavel ON solicitacao_descarte(empresa_responsavel_id, estado)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_oferta_aceita_solicitacao ON oferta_coleta(solicitacao_id) WHERE status = 'ACEITA'")
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_atribuicao_consistente
        BEFORE UPDATE OF empresa_responsavel_id, base_operacional_id ON solicitacao_descarte
        WHEN NEW.empresa_responsavel_id IS NOT NULL AND (
            NEW.base_operacional_id IS NULL OR NOT EXISTS (
                SELECT 1 FROM base_operacional b
                WHERE b.id = NEW.base_operacional_id
                  AND b.empresa_id = NEW.empresa_responsavel_id
            )
        )
        BEGIN
            SELECT RAISE(ABORT, 'base nao pertence a empresa responsavel');
        END
    """)
