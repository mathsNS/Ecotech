"""Migration 001: unicidade, vínculos e validações essenciais."""


def _validar_sem_duplicatas(conn, tabela, coluna) -> None:
    row = conn.execute(
        f"SELECT {coluna}, COUNT(*) AS total FROM {tabela} "
        f"WHERE {coluna} IS NOT NULL AND TRIM({coluna}) <> '' "
        f"GROUP BY {coluna} HAVING COUNT(*) > 1 LIMIT 1"
    ).fetchone()
    if row:
        raise RuntimeError(
            f"Migration bloqueada: {tabela}.{coluna} possui valor duplicado"
        )


def aplicar(conn) -> None:
    for tabela, coluna, indice in (
        ("usuario", "email", "uq_usuario_email"),
        ("cidadao", "cpf", "uq_cidadao_cpf"),
        ("empresa", "cnpj", "uq_empresa_cnpj"),
    ):
        _validar_sem_duplicatas(conn, tabela, coluna)
        conn.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {indice} "
            f"ON {tabela}({coluna}) WHERE {coluna} IS NOT NULL AND TRIM({coluna}) <> ''"
        )

    for comando in (
        "CREATE INDEX IF NOT EXISTS idx_ponto_empresa ON ponto_coleta(id_empresa)",
        "CREATE INDEX IF NOT EXISTS idx_solicitacao_ponto ON solicitacao_descarte(id_ponto_coleta)",
        "CREATE INDEX IF NOT EXISTS idx_solicitacao_estado ON solicitacao_descarte(estado)",
        """CREATE TRIGGER IF NOT EXISTS trg_ponto_empresa_insert
        BEFORE INSERT ON ponto_coleta
        WHEN NEW.id_empresa IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM empresa WHERE id_usuario = NEW.id_empresa)
        BEGIN
            SELECT RAISE(ABORT, 'empresa do ponto de coleta inexistente');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_ponto_empresa_update
        BEFORE UPDATE OF id_empresa ON ponto_coleta
        WHEN NEW.id_empresa IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM empresa WHERE id_usuario = NEW.id_empresa)
        BEGIN
            SELECT RAISE(ABORT, 'empresa do ponto de coleta inexistente');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_item_valido_insert
        BEFORE INSERT ON item_descarte
        WHEN NEW.quantidade <= 0
        BEGIN
            SELECT RAISE(ABORT, 'quantidade deve ser positiva');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_item_valido_update
        BEFORE UPDATE OF quantidade ON item_descarte
        WHEN NEW.quantidade <= 0
        BEGIN
            SELECT RAISE(ABORT, 'quantidade deve ser positiva');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_dispositivo_peso_insert
        BEFORE INSERT ON dispositivo
        WHEN NEW.peso_kg <= 0
        BEGIN
            SELECT RAISE(ABORT, 'peso deve ser positivo');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_dispositivo_peso_update
        BEFORE UPDATE OF peso_kg ON dispositivo
        WHEN NEW.peso_kg <= 0
        BEGIN
            SELECT RAISE(ABORT, 'peso deve ser positivo');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_ponto_capacidade_insert
        BEFORE INSERT ON ponto_coleta
        WHEN NEW.capacidade_kg <= 0 OR NEW.ocupacao_atual_kg < 0
             OR NEW.ocupacao_atual_kg > NEW.capacidade_kg
        BEGIN
            SELECT RAISE(ABORT, 'capacidade ou ocupacao invalida');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_ponto_capacidade_update
        BEFORE UPDATE OF capacidade_kg, ocupacao_atual_kg ON ponto_coleta
        WHEN NEW.capacidade_kg <= 0 OR NEW.ocupacao_atual_kg < 0
             OR NEW.ocupacao_atual_kg > NEW.capacidade_kg
        BEGIN
            SELECT RAISE(ABORT, 'capacidade ou ocupacao invalida');
        END""",
    ):
        conn.execute(comando)
