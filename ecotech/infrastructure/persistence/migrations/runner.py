"""Executor pequeno e transacional de migrations SQLite."""

from datetime import datetime, timezone

from .v001_integridade_basica import aplicar as aplicar_v001
from .v002_idempotencia_financeira import aplicar as aplicar_v002
from .v003_bases_localizacao import aplicar as aplicar_v003
from .v004_elegibilidade_ranking import aplicar as aplicar_v004
from .v005_ofertas_despacho import aplicar as aplicar_v005
from .v006_aceite_atribuicao import aplicar as aplicar_v006
from .v007_agendamento import aplicar as aplicar_v007


MIGRATIONS = (
    (1, "integridade_basica", aplicar_v001),
    (2, "idempotencia_financeira", aplicar_v002),
    (3, "bases_operacionais_localizacao", aplicar_v003),
    (4, "elegibilidade_ranking", aplicar_v004),
    (5, "ofertas_despacho_progressivo", aplicar_v005),
    (6, "aceite_atribuição_atomica", aplicar_v006),
    (7, "negociacao_agendamento", aplicar_v007),
)


def _criar_tabela_controle(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migration (
            versao INTEGER PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE,
            aplicada_em TEXT NOT NULL
        )
    """)


def versao_atual(conn) -> int:
    _criar_tabela_controle(conn)
    row = conn.execute(
        "SELECT COALESCE(MAX(versao), 0) AS versao FROM schema_migration"
    ).fetchone()
    return int(row["versao"] if hasattr(row, "keys") else row[0])


def executar_migrations(conn) -> None:
    """Executa uma única vez cada migration, em transação individual."""
    _criar_tabela_controle(conn)
    aplicadas = {
        row[0] for row in conn.execute("SELECT versao FROM schema_migration")
    }

    for versao, nome, aplicar in MIGRATIONS:
        if versao in aplicadas:
            continue
        with conn:
            aplicar(conn)
            conn.execute(
                "INSERT INTO schema_migration (versao, nome, aplicada_em) "
                "VALUES (?, ?, ?)",
                (versao, nome, datetime.now(timezone.utc).isoformat()),
            )
