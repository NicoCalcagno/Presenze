from datetime import date, time

import pytest

from presenze import calcolo
from presenze.calcolo import Contratto, Giornata


def test_minuti_lavorati_con_pausa_oltre_sei_ore() -> None:
    assert calcolo.minuti_lavorati(time(9), time(13)) == 240
    assert calcolo.minuti_lavorati(time(8, 30), time(17)) == 8 * 60 + 30 - calcolo.PAUSA


def test_uscita_prima_dell_entrata() -> None:
    with pytest.raises(ValueError):
        calcolo.minuti_lavorati(time(17), time(9))


def test_riepilogo_tempo_pieno() -> None:
    giornate = [
        Giornata(date(2026, 10, 5), 8 * 60),  # lunedì
        Giornata(date(2026, 10, 6), 9 * 60),  # martedì: un'ora di straordinario
        Giornata(date(2026, 10, 10), 4 * 60),  # sabato
    ]
    r = calcolo.riepilogo("2026-10", Contratto(40), giornate)
    assert (r.giorni_lavorati, r.minuti_ordinari, r.minuti_straordinari, r.minuti_festivi) == (
        3,
        16 * 60,
        60,
        4 * 60,
    )


def test_riepilogo_festivo_infrasettimanale() -> None:
    r = calcolo.riepilogo("2026-11", Contratto(40), [Giornata(date(2026, 11, 2), 300, True)])
    assert (r.minuti_ordinari, r.minuti_festivi) == (0, 300)
