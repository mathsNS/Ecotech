"""Migration 002: vínculo e idempotência dos lançamentos financeiros."""


def _coluna_existe(conn, tabela, coluna) -> bool:
    return any(row[1] == coluna for row in conn.execute(f"PRAGMA table_info({tabela})"))


def aplicar(conn) -> None:
    if not _coluna_existe(conn, "entrega", "id_solicitacao"):
        conn.execute("ALTER TABLE entrega ADD COLUMN id_solicitacao TEXT")

    duplicada = conn.execute("""
        SELECT id_solicitacao, COUNT(*) AS total
        FROM receita_ecotech
        WHERE id_solicitacao IS NOT NULL
        GROUP BY id_solicitacao
        HAVING COUNT(*) > 1
        LIMIT 1
    """).fetchone()
    if duplicada:
        raise RuntimeError(
            "Migration bloqueada: há mais de uma receita para a mesma solicitação"
        )

    for comando in (
        """CREATE UNIQUE INDEX IF NOT EXISTS uq_entrega_solicitacao
            ON entrega(id_solicitacao)
            WHERE id_solicitacao IS NOT NULL""",
        """CREATE UNIQUE INDEX IF NOT EXISTS uq_receita_solicitacao
            ON receita_ecotech(id_solicitacao)
            WHERE id_solicitacao IS NOT NULL""",
        "CREATE INDEX IF NOT EXISTS idx_receita_solicitacao ON receita_ecotech(id_solicitacao)",
        """CREATE TRIGGER IF NOT EXISTS trg_entrega_valor_insert
        BEFORE INSERT ON entrega
        WHEN NEW.valor < 0
        BEGIN
            SELECT RAISE(ABORT, 'valor da entrega nao pode ser negativo');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_saque_valor_insert
        BEFORE INSERT ON saque
        WHEN NEW.valor <= 0
        BEGIN
            SELECT RAISE(ABORT, 'valor do saque deve ser positivo');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_receita_valor_insert
        BEFORE INSERT ON receita_ecotech
        WHEN NEW.valor < 0
        BEGIN
            SELECT RAISE(ABORT, 'receita nao pode ser negativa');
        END""",
        """CREATE TRIGGER IF NOT EXISTS trg_entrega_solicitacao_insert
        BEFORE INSERT ON entrega
        WHEN NEW.id_solicitacao IS NOT NULL
             AND NOT EXISTS (
                 SELECT 1 FROM solicitacao_descarte WHERE id = NEW.id_solicitacao
             )
        BEGIN
            SELECT RAISE(ABORT, 'solicitacao da entrega inexistente');
        END""",
    ):
        conn.execute(comando)
