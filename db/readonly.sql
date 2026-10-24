-- Utente in sola lettura per il Data investigator di Solvo (`PRESENZE_RO_DSN`).
-- pg_monitor serve ai controlli di salute (connessioni, lock, query lente).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solvo_ro') THEN
        CREATE ROLE solvo_ro LOGIN PASSWORD 'solvo_ro';
    END IF;
END
$$;
GRANT CONNECT ON DATABASE presenze TO solvo_ro;
GRANT USAGE ON SCHEMA public TO solvo_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO solvo_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO solvo_ro;
GRANT pg_monitor TO solvo_ro;
ALTER ROLE solvo_ro SET default_transaction_read_only = on;
