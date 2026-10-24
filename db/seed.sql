-- Dati di esempio (persone inventate). Idempotente.

INSERT INTO reparti (nome) VALUES
    ('Amministrazione'), ('Sviluppo'), ('Commerciale'), ('Logistica'), ('Risorse umane')
ON CONFLICT (nome) DO NOTHING;

-- 60 dipendenti: uno su tre part-time (20, 24 o 30 ore).
INSERT INTO dipendenti (matricola, nome_cognome, email, codice_fiscale, reparto_id, ore_settimanali)
SELECT
    'M' || lpad(i::text, 4, '0'),
    (ARRAY['Giulia','Marco','Sara','Luca','Chiara','Paolo','Elena','Davide','Anna','Fabio'])[1 + i % 10]
        || ' ' ||
    (ARRAY['Rossi','Bianchi','Ferri','Conti','Greco','Marino','Gallo','Costa','Fontana','Riva'])[1 + (i / 10) % 10],
    'dipendente' || i || '@azienda.it',
    'XXXXXX00A00X' || lpad(i::text, 3, '0') || 'X',
    1 + i % 5,
    CASE WHEN i % 3 = 0 THEN (ARRAY[20, 24, 30])[1 + (i / 3) % 3] ELSE 40 END
FROM generate_series(1, 60) AS i
ON CONFLICT (matricola) DO NOTHING;

INSERT INTO festivi (giorno, nome) VALUES
    ('2026-01-01', 'Capodanno'), ('2026-01-06', 'Epifania'), ('2026-04-06', 'Pasquetta'),
    ('2026-04-25', 'Liberazione'), ('2026-05-01', 'Festa del lavoro'),
    ('2026-06-02', 'Festa della Repubblica'), ('2026-08-15', 'Ferragosto'),
    ('2026-11-01', 'Ognissanti'), ('2026-12-08', 'Immacolata'), ('2026-12-25', 'Natale'),
    ('2026-12-26', 'Santo Stefano')
ON CONFLICT (giorno) DO NOTHING;

-- Timbrature dei giorni lavorativi dal primo del mese scorso a ieri: entrata tra le 8 e le 9,
-- uscita dopo l'orario del contratto, a volte con straordinario.
INSERT INTO timbrature (dipendente_id, giorno, entrata, uscita)
SELECT
    d.id,
    g::date,
    time '08:00' + (d.id * 7 % 60) * interval '1 minute',
    time '08:00' + (d.id * 7 % 60) * interval '1 minute'
        + (d.ore_settimanali * 12 + CASE WHEN d.ore_settimanali * 12 > 360 THEN 30 ELSE 0 END)
          * interval '1 minute'
        + ((d.id + extract(day FROM g)::int) % 4) * 15 * interval '1 minute'
FROM dipendenti d
CROSS JOIN generate_series(
    date_trunc('month', current_date) - interval '1 month', current_date - 1, interval '1 day'
) AS g
WHERE extract(isodow FROM g) < 6
ON CONFLICT (dipendente_id, giorno) DO NOTHING;
