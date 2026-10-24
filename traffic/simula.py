"""Dipendenti finti: timbrano, guardano il riepilogo del mese, i responsabili controllano
chi è presente. Solo libreria standard.

Uso: `python traffic/simula.py [--url http://localhost:8090] [--rate 2]` (richieste al
secondo, circa).
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from datetime import date

DIPENDENTI = 60
REPARTI = 5


def call(url: str, method: str = "GET") -> int:
    request = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            json.loads(response.read() or b"null")
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, TimeoutError):
        return 0


def visita(base: str) -> int:
    dipendente = random.randint(1, DIPENDENTI)
    scelta = random.random()
    if scelta < 0.6:
        mese = date.today().strftime("%Y-%m")
        if random.random() < 0.3:  # il mese scorso
            primo = date.today().replace(day=1)
            mese = date.fromordinal(primo.toordinal() - 1).strftime("%Y-%m")
        return call(f"{base}/api/dipendenti/{dipendente}/riepilogo?mese={mese}")
    if scelta < 0.8:
        return call(f"{base}/api/dipendenti/{dipendente}")
    if scelta < 0.9:
        return call(f"{base}/api/reparti/{random.randint(1, REPARTI)}/presenti-oggi")
    return call(f"{base}/api/dipendenti/{dipendente}/timbra", "POST")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8090")
    parser.add_argument("--rate", type=float, default=2.0)
    args = parser.parse_args()
    base = args.url.rstrip("/")
    print(f"traffico verso {base}, circa {args.rate} richieste al secondo (Ctrl+C per smettere)")
    while True:
        if visita(base) == 0:
            print("Presenze non risponde, riprovo tra 5 s")
            time.sleep(5)
        time.sleep(random.expovariate(args.rate))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
