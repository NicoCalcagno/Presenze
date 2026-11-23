from datetime import date

from presenze.calcolo import Contratto, Giornata, riepilogo


def test_riepilogo_part_time_non_va_in_errore_sui_festivi() -> None:
    r = riepilogo("2027-11", Contratto(20), [Giornata(date(2027, 11, 1), 240, True)])

    assert r.minuti_festivi == 240
    assert r.minuti_festivi_maggiorati == 360
