"""Migration 003: bases operacionais e localização da coleta."""


def _coluna_existe(conn, tabela, coluna) -> bool:
    return any(row[1] == coluna for row in conn.execute(f"PRAGMA table_info({tabela})"))


def aplicar(conn) -> None:
    for coluna, definicao in (
        ('latitude_coleta', 'REAL'),
        ('longitude_coleta', 'REAL'),
        ('localizacao_obtida_em', 'TEXT'),
        ('origem_localizacao', 'TEXT'),
    ):
        if not _coluna_existe(conn, 'solicitacao_descarte', coluna):
            conn.execute(
                f"ALTER TABLE solicitacao_descarte ADD COLUMN {coluna} {definicao}"
            )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS base_operacional (
            id TEXT PRIMARY KEY,
            empresa_id TEXT NOT NULL,
            ponto_coleta_id TEXT,
            nome TEXT NOT NULL,
            endereco TEXT NOT NULL,
            latitude REAL NOT NULL CHECK(latitude BETWEEN -90 AND 90),
            longitude REAL NOT NULL CHECK(longitude BETWEEN -180 AND 180),
            raio_atendimento_km REAL NOT NULL CHECK(raio_atendimento_km > 0),
            capacidade_kg REAL NOT NULL CHECK(capacidade_kg > 0),
            ocupacao_atual_kg REAL NOT NULL DEFAULT 0
                CHECK(ocupacao_atual_kg >= 0 AND ocupacao_atual_kg <= capacidade_kg),
            realiza_coleta_domiciliar INTEGER NOT NULL DEFAULT 1
                CHECK(realiza_coleta_domiciliar IN (0, 1)),
            ativa INTEGER NOT NULL DEFAULT 1 CHECK(ativa IN (0, 1)),
            criada_em TEXT NOT NULL,
            atualizada_em TEXT NOT NULL,
            FOREIGN KEY(empresa_id) REFERENCES empresa(id_usuario),
            FOREIGN KEY(ponto_coleta_id) REFERENCES ponto_coleta(id)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_base_empresa_ativa "
        "ON base_operacional(empresa_id, ativa)"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_base_ponto "
        "ON base_operacional(ponto_coleta_id) WHERE ponto_coleta_id IS NOT NULL"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_solicitacao_localizacao "
        "ON solicitacao_descarte(latitude_coleta, longitude_coleta)"
    )
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_solicitacao_coordenadas_insert
        BEFORE INSERT ON solicitacao_descarte
        WHEN (NEW.latitude_coleta IS NOT NULL AND
              (NEW.latitude_coleta < -90 OR NEW.latitude_coleta > 90))
          OR (NEW.longitude_coleta IS NOT NULL AND
              (NEW.longitude_coleta < -180 OR NEW.longitude_coleta > 180))
        BEGIN
            SELECT RAISE(ABORT, 'coordenadas de coleta invalidas');
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_solicitacao_coordenadas_update
        BEFORE UPDATE OF latitude_coleta, longitude_coleta ON solicitacao_descarte
        WHEN (NEW.latitude_coleta IS NOT NULL AND
              (NEW.latitude_coleta < -90 OR NEW.latitude_coleta > 90))
          OR (NEW.longitude_coleta IS NOT NULL AND
              (NEW.longitude_coleta < -180 OR NEW.longitude_coleta > 180))
        BEGIN
            SELECT RAISE(ABORT, 'coordenadas de coleta invalidas');
        END
    """)

    # Cada ponto empresarial existente origina uma base inicial auditável.
    conn.execute("""
        INSERT OR IGNORE INTO base_operacional (
            id, empresa_id, ponto_coleta_id, nome, endereco,
            latitude, longitude, raio_atendimento_km,
            capacidade_kg, ocupacao_atual_kg,
            realiza_coleta_domiciliar, ativa, criada_em, atualizada_em
        )
        SELECT 'base-' || pc.id, pc.id_empresa, pc.id, pc.nome, pc.endereco,
               pc.latitude, pc.longitude, 25.0,
               pc.capacidade_kg, pc.ocupacao_atual_kg,
               1, pc.ativo, datetime('now'), datetime('now')
        FROM ponto_coleta pc
        WHERE pc.id_empresa IS NOT NULL
    """)
