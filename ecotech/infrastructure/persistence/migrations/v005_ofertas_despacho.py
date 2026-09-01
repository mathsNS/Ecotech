"""Migration 005: ofertas persistentes e despacho progressivo."""


def _coluna_existe(conn, tabela, coluna) -> bool:
    return any(row[1] == coluna for row in conn.execute(f"PRAGMA table_info({tabela})"))


def aplicar(conn) -> None:
    if not _coluna_existe(conn, 'notificacao', 'chave_idempotencia'):
        conn.execute("ALTER TABLE notificacao ADD COLUMN chave_idempotencia TEXT")
    if not _coluna_existe(conn, 'solicitacao_descarte', 'despacho_esgotado_em'):
        conn.execute("ALTER TABLE solicitacao_descarte ADD COLUMN despacho_esgotado_em TEXT")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS oferta_coleta (
            id TEXT PRIMARY KEY,
            solicitacao_id TEXT NOT NULL,
            empresa_id TEXT NOT NULL,
            base_operacional_id TEXT NOT NULL,
            distancia_km REAL NOT NULL CHECK(distancia_km >= 0),
            score_prioridade REAL NOT NULL,
            prioridade INTEGER NOT NULL CHECK(prioridade > 0),
            rodada INTEGER NOT NULL CHECK(rodada > 0),
            status TEXT NOT NULL CHECK(status IN (
                'AGUARDANDO', 'ATIVA', 'ACEITA', 'RECUSADA', 'EXPIRADA', 'CANCELADA'
            )),
            snapshot_fatores TEXT NOT NULL,
            enviada_em TEXT,
            ativada_em TEXT,
            expira_em TEXT,
            respondida_em TEXT,
            motivo_recusa TEXT,
            criada_em TEXT NOT NULL,
            FOREIGN KEY(solicitacao_id) REFERENCES solicitacao_descarte(id),
            FOREIGN KEY(empresa_id) REFERENCES empresa(id_usuario),
            FOREIGN KEY(base_operacional_id) REFERENCES base_operacional(id),
            UNIQUE(solicitacao_id, base_operacional_id),
            UNIQUE(solicitacao_id, prioridade)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_oferta_empresa_status ON oferta_coleta(empresa_id, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_oferta_solicitacao_status ON oferta_coleta(solicitacao_id, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_oferta_expiracao ON oferta_coleta(status, expira_em)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_notificacao_chave ON notificacao(chave_idempotencia) WHERE chave_idempotencia IS NOT NULL")
