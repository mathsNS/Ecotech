"""Migration 013: registra o ano de fabricacao informado pelo cidadao."""


def aplicar(conn):
    colunas = {row[1] for row in conn.execute("PRAGMA table_info(dispositivo)")}
    if 'ano_fabricacao' not in colunas:
        conn.execute("ALTER TABLE dispositivo ADD COLUMN ano_fabricacao INTEGER")
