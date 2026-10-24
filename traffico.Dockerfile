# Dipendenti finti come servizio a sé (su Railway): PRESENZE_URL è l'indirizzo dell'app.
FROM python:3.12-slim
COPY traffic/simula.py /simula.py
CMD ["sh", "-c", "python -u /simula.py --url \"$PRESENZE_URL\" --rate \"${TRAFFIC_RATE:-2}\""]
