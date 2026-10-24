FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /bin/uv
# /srv/app: gli stack trace nei log hanno percorsi come /srv/app/presenze/calcolo.py,
# che Solvo riconduce al file del repository.
WORKDIR /srv/app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/srv/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY presenze ./presenze
COPY db ./db
RUN uv sync --frozen --no-dev

ARG PRESENZE_VERSION=dev
ENV PRESENZE_VERSION=${PRESENZE_VERSION}
EXPOSE 8080
# Host vuoto: tutte le interfacce, IPv4 e IPv6 (la rete privata di Railway usa IPv6, l'ingresso
# pubblico IPv4). Con `::` asyncio ascolta solo su IPv6.
CMD ["uvicorn", "presenze.app:app", "--host", "", "--port", "8080"]
