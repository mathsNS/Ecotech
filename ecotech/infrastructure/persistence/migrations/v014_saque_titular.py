"""Migration 14: adiciona titular e criado_em ISO na tabela saque."""


def _coluna_existe(conn, tabela: str, coluna: str) -> bool:
    return any(
        row[1] == coluna for row in conn.execute(f"PRAGMA table_info({tabela})")
    )


def aplicar(conn) -> None:
    if not _coluna_existe(conn, "saque", "titular"):
        conn.execute(
            "ALTER TABLE saque ADD COLUMN titular TEXT NOT NULL DEFAULT ''"
        )
    if not _coluna_existe(conn, "saque", "criado_em"):
        conn.execute("ALTER TABLE saque ADD COLUMN criado_em TEXT")
