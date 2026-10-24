"""Accesso a Postgres (psycopg 3, pool di connessioni). Schema e dati finti all'avvio."""

from __future__ import annotations

import os
from pathlib import Path

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DSN = os.environ.get("DATABASE_URL", "postgresql://presenze:presenze@localhost:5433/presenze")
SQL = Path(__file__).resolve().parent.parent / "db"

pool = ConnectionPool(
    DSN,
    min_size=1,
    max_size=int(os.environ.get("DB_POOL_SIZE", "10")),
    # Attesa massima per una connessione libera.
    timeout=float(os.environ.get("DB_POOL_TIMEOUT", "10")),
    kwargs={"row_factory": dict_row},
    open=False,
)


def init() -> None:
    """Apre il pool e applica schema, dati finti e utente in sola lettura (idempotenti)."""
    pool.open(wait=True, timeout=30)
    with pool.connection() as conn:
        for name in ("schema.sql", "seed.sql", "readonly.sql"):
            conn.execute((SQL / name).read_text())
