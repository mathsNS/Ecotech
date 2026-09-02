"""Migration 012: separa peso estimado do peso aferido no recebimento."""


def aplicar(conn):
    colunas = {row[1] for row in conn.execute("PRAGMA table_info(solicitacao_descarte)")}
    for nome, definicao in (
        ('peso_estimado_kg', 'REAL'),
        ('peso_informado_cidadao', 'INTEGER NOT NULL DEFAULT 1'),
        ('peso_confirmado_kg', 'REAL'),
        ('peso_confirmado_em', 'TEXT'),
        ('peso_confirmado_por', 'TEXT'),
    ):
        if nome not in colunas:
            conn.execute(f"ALTER TABLE solicitacao_descarte ADD COLUMN {nome} {definicao}")
    conn.execute("""UPDATE solicitacao_descarte SET peso_estimado_kg=(
        SELECT COALESCE(SUM(i.quantidade*d.peso_kg),0) FROM item_descarte i
        JOIN dispositivo d ON d.id=i.id_dispositivo WHERE i.id_solicitacao=solicitacao_descarte.id
    ) WHERE peso_estimado_kg IS NULL""")
    conn.execute("""UPDATE solicitacao_descarte SET peso_confirmado_kg=peso_estimado_kg
        WHERE peso_confirmado_kg IS NULL AND estado IN ('RECICLADO','REUTILIZADO','DESCARTADO')""")
