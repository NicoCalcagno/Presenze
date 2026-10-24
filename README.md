# Presenze

Gestionale interno di timbrature e ore lavorate: i dipendenti timbrano entrata e uscita e
vedono il riepilogo del mese (ore ordinarie, straordinari, ore nei festivi), i responsabili
vedono chi è presente. FastAPI e Postgres, log in Loki, CI e deploy con GitHub Actions.
Lo segue Solvo (ticket, incident, rilasci).

## Avvio sul Mac

Prima Solvo (`make up` nel repository di Solvo: serve il suo collector OTel su `:4318`).

```bash
PRESENZE_VERSION=$(git rev-parse --short=12 HEAD) docker compose up -d --build
curl localhost:8090/health
docker compose --profile traffico up -d      # dipendenti finti, ~2 richieste al secondo
```

- API: http://localhost:8090 (`/docs` per l'elenco)
- Postgres: `localhost:5434`, utente `presenze`/`presenze`; in sola lettura `solvo_ro`/`solvo_ro`
- Log: in Loki con `{service="presenze", env="prod"}`

## Sviluppo

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
DATABASE_URL=postgresql://presenze:presenze@localhost:5434/presenze uv run pytest
```

## Deploy

Il workflow `deploy` gira a ogni push su `main` e a mano (*Run workflow*, con un commit
nell'input `version`: così Solvo fa il rollback) su un runner self-hosted con l'etichetta
`presenze`:

1. GitHub → *Settings → Actions → Runners → New self-hosted runner* → macOS, e i comandi
   indicati (download e `./config.sh`); alla domanda sulle etichette aggiungere `presenze`.
2. Avviarlo con `./run.sh`, con Docker Desktop acceso.

Il runner lancia `docker compose up -d --build app` nel proprio checkout; il progetto Compose
si chiama sempre `presenze`, quindi sostituisce i container avviati a mano.
