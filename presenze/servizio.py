"""Dipendenti, timbrature e riepiloghi sopra il database."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any

from psycopg import Connection

from presenze import calcolo


class NonTrovato(Exception):
    pass


class NonValido(Exception):
    pass


def dipendente(conn: Connection, dipendente_id: int) -> dict[str, Any]:
    row = conn.execute(
        """SELECT d.id, d.matricola, d.nome_cognome, r.nome AS reparto, d.ore_settimanali
           FROM dipendenti d JOIN reparti r ON r.id = d.reparto_id WHERE d.id = %s""",
        (dipendente_id,),
    ).fetchone()
    if row is None:
        raise NonTrovato(f"dipendente {dipendente_id} inesistente")
    return row


def timbra(conn: Connection, dipendente_id: int, adesso: datetime) -> dict[str, Any]:
    """Prima timbratura del giorno: entrata; la seconda: uscita."""
    dipendente(conn, dipendente_id)
    with conn.transaction():
        oggi = conn.execute(
            "SELECT id, uscita FROM timbrature WHERE dipendente_id = %s AND giorno = %s FOR UPDATE",
            (dipendente_id, adesso.date()),
        ).fetchone()
        if oggi is None:
            conn.execute(
                "INSERT INTO timbrature (dipendente_id, giorno, entrata) VALUES (%s, %s, %s)",
                (dipendente_id, adesso.date(), adesso.time()),
            )
            return {"tipo": "entrata", "ora": adesso.time().isoformat("minutes")}
        if oggi["uscita"] is not None:
            raise NonValido("entrata e uscita di oggi già registrate")
        conn.execute("UPDATE timbrature SET uscita = %s WHERE id = %s", (adesso.time(), oggi["id"]))
        return {"tipo": "uscita", "ora": adesso.time().isoformat("minutes")}


def riepilogo(conn: Connection, dipendente_id: int, mese: str) -> calcolo.Riepilogo:
    try:
        inizio = date.fromisoformat(f"{mese}-01")
    except ValueError as exc:
        raise NonValido("mese nel formato AAAA-MM") from exc
    fine = date(inizio.year + inizio.month // 12, inizio.month % 12 + 1, 1)
    contratto = calcolo.Contratto(dipendente(conn, dipendente_id)["ore_settimanali"])
    righe = conn.execute(
        """SELECT t.giorno, t.entrata, t.uscita, f.giorno IS NOT NULL AS festivo
           FROM timbrature t LEFT JOIN festivi f ON f.giorno = t.giorno
           WHERE t.dipendente_id = %s AND t.giorno >= %s AND t.giorno < %s AND t.uscita > t.entrata
           ORDER BY t.giorno""",
        (dipendente_id, inizio, fine),
    ).fetchall()
    giornate = [
        calcolo.Giornata(
            r["giorno"], calcolo.minuti_lavorati(r["entrata"], r["uscita"]), r["festivo"]
        )
        for r in righe
    ]
    return calcolo.riepilogo(mese, contratto, giornate)


def minuti_previsti(conn: Connection, dipendente_id: int, mese: str) -> int:
    """Minuti da contratto nel mese: i giorni dal lunedì al venerdì per l'orario giornaliero."""
    inizio = date.fromisoformat(f"{mese}-01")
    ultimo = inizio.replace(day=calendar.monthrange(inizio.year, inizio.month)[1])
    feriali = sum(
        1
        for giorno in range(1, ultimo.day + 1)
        if inizio.replace(day=giorno).weekday() < calcolo.GIORNI_LAVORATIVI
    )
    contratto = calcolo.Contratto(dipendente(conn, dipendente_id)["ore_settimanali"])
    return feriali * contratto.minuti_giornalieri


def presenti_oggi(conn: Connection, reparto_id: int, oggi: date) -> list[dict[str, Any]]:
    return conn.execute(
        """SELECT d.id, d.matricola, t.entrata, t.uscita
           FROM dipendenti d JOIN timbrature t ON t.dipendente_id = d.id AND t.giorno = %s
           WHERE d.reparto_id = %s ORDER BY t.entrata""",
        (oggi, reparto_id),
    ).fetchall()
