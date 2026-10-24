"""API di Presenze (FastAPI). Ogni richiesta lascia una riga di log; un errore inatteso
lascia anche lo stack trace (`exception`)."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from presenze import VERSION, db, logs, servizio

logger = logging.getLogger("presenze")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logs.setup()
    db.init()
    logs.log(logger, logging.INFO, "presenze avviata", event="startup")
    yield
    db.pool.close()
    logs.shutdown()


app = FastAPI(title="Presenze", version=VERSION, lifespan=lifespan)


@app.middleware("http")
async def access_log(request: Request, call_next):  # type: ignore[no-untyped-def]
    start = time.perf_counter()
    fields = {"method": request.method, "path": request.url.path}
    try:
        response = await call_next(request)
    except Exception:
        duration = round((time.perf_counter() - start) * 1000, 1)
        logger.exception(
            "errore inatteso", extra={"fields": {**fields, "status": 500, "duration_ms": duration}}
        )
        return JSONResponse({"detail": "errore interno"}, status_code=500)
    duration = round((time.perf_counter() - start) * 1000, 1)
    if request.url.path != "/health":
        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logs.log(
            logger,
            level,
            "richiesta http",
            **fields,
            status=response.status_code,
            duration_ms=duration,
        )
    return response


@app.exception_handler(servizio.NonTrovato)
async def _non_trovato(_: Request, exc: servizio.NonTrovato) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.exception_handler(servizio.NonValido)
async def _non_valido(_: Request, exc: servizio.NonValido) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=422)


@app.get("/health")
def health() -> dict[str, str]:
    with db.pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "version": VERSION}


@app.get("/api/dipendenti/{dipendente_id}")
def dipendente(dipendente_id: int) -> dict:
    with db.pool.connection() as conn:
        return servizio.dipendente(conn, dipendente_id)


@app.post("/api/dipendenti/{dipendente_id}/timbra")
def timbra(dipendente_id: int) -> dict:
    with db.pool.connection() as conn:
        return servizio.timbra(conn, dipendente_id, datetime.now())


@app.get("/api/dipendenti/{dipendente_id}/riepilogo")
def riepilogo(dipendente_id: int, mese: str | None = None) -> dict:
    with db.pool.connection() as conn:
        mese = mese or date.today().strftime("%Y-%m")
        return servizio.riepilogo(conn, dipendente_id, mese).__dict__


@app.get("/api/reparti/{reparto_id}/presenti-oggi")
def presenti_oggi(reparto_id: int) -> list[dict]:
    with db.pool.connection() as conn:
        return servizio.presenti_oggi(conn, reparto_id, date.today())
