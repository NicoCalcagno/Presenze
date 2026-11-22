"""Calcolo delle ore: minuti lavorati da una timbratura e riepilogo del mese (ordinarie,
straordinari, ore nei festivi) sul contratto del dipendente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

GIORNI_LAVORATIVI = 5  # dal lunedì al venerdì
PAUSA_OLTRE = 6 * 60  # oltre 6 ore di lavoro si toglie la pausa
PAUSA = 30


@dataclass(frozen=True)
class Contratto:
    ore_settimanali: int  # 40 tempo pieno; 20, 24, 30 part-time

    @property
    def minuti_giornalieri(self) -> int:
        return self.ore_settimanali * 60 // GIORNI_LAVORATIVI


@dataclass(frozen=True)
class Giornata:
    giorno: date
    minuti: int
    festivo: bool = False


@dataclass(frozen=True)
class Riepilogo:
    mese: str
    giorni_lavorati: int
    minuti_ordinari: int
    minuti_straordinari: int
    minuti_festivi: int


def minuti_lavorati(entrata: time, uscita: time) -> int:
    inizio = datetime.combine(date.min, entrata)
    fine = datetime.combine(date.min, uscita)
    if fine <= inizio:
        raise ValueError("uscita prima dell'entrata")
    minuti = int((fine - inizio).total_seconds() // 60)
    return minuti - PAUSA if minuti > PAUSA_OLTRE else minuti


def riepilogo(mese: str, contratto: Contratto, giornate: list[Giornata]) -> Riepilogo:
    ordinari = straordinari = festivi = 0
    for giornata in giornate:
        if giornata.festivo or giornata.giorno.weekday() >= GIORNI_LAVORATIVI:
            festivi += giornata.minuti
            continue
        ordinari += min(giornata.minuti, contratto.minuti_giornalieri)
        straordinari += max(giornata.minuti - contratto.minuti_giornalieri, 0)
    return Riepilogo(
        mese=mese,
        giorni_lavorati=sum(1 for g in giornate if g.minuti > 0),
        minuti_ordinari=ordinari,
        minuti_straordinari=straordinari,
        minuti_festivi=festivi,
    )
