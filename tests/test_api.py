"""Prove dell'API su Postgres vero (`DATABASE_URL`, in CI un servizio del job)."""

import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="serve Postgres (DATABASE_URL)"
)


@pytest.fixture(scope="module")
def client():
    from presenze.app import app

    with TestClient(app) as client:
        yield client


def test_health(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_dipendente(client: TestClient) -> None:
    assert client.get("/api/dipendenti/1").json()["matricola"] == "M0001"
    assert client.get("/api/dipendenti/9999").status_code == 404


def test_riepilogo_del_mese(client: TestClient) -> None:
    r = client.get("/api/dipendenti/1/riepilogo")
    assert r.status_code == 200, r.text
    assert r.json()["minuti_ordinari"] >= 0
    assert r.json()["minuti_previsti"] > 0
    assert client.get("/api/dipendenti/1/riepilogo?mese=ottobre").status_code == 422


def test_timbra_entrata_e_uscita(client: TestClient) -> None:
    # dipendente senza timbrature di oggi: i dati di esempio arrivano a ieri
    first = client.post("/api/dipendenti/2/timbra")
    if first.status_code == 422:  # test già girato oggi sullo stesso database
        return
    assert first.json()["tipo"] == "entrata"
    assert client.post("/api/dipendenti/2/timbra").json()["tipo"] == "uscita"
    assert client.post("/api/dipendenti/2/timbra").status_code == 422
