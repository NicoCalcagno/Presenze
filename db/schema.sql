-- Schema di Presenze. Idempotente: lo applica l'app all'avvio.

CREATE TABLE IF NOT EXISTS reparti (
    id   SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dipendenti (
    id              SERIAL PRIMARY KEY,
    matricola       TEXT NOT NULL UNIQUE,
    -- Colonne personali: Solvo le dichiara in `db_config.pii_columns` e non le mostra mai.
    nome_cognome    TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    codice_fiscale  TEXT NOT NULL UNIQUE,
    reparto_id      INTEGER NOT NULL REFERENCES reparti(id),
    ore_settimanali INTEGER NOT NULL CHECK (ore_settimanali BETWEEN 8 AND 40)
);

CREATE TABLE IF NOT EXISTS festivi (
    giorno DATE PRIMARY KEY,
    nome   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS timbrature (
    id            BIGSERIAL PRIMARY KEY,
    dipendente_id INTEGER NOT NULL REFERENCES dipendenti(id),
    giorno        DATE NOT NULL,
    entrata       TIME NOT NULL,
    uscita        TIME,
    UNIQUE (dipendente_id, giorno)
);
CREATE INDEX IF NOT EXISTS ix_timbrature_giorno ON timbrature (giorno);
