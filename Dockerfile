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
CMD ["uvicorn", "presenze.app:app", "--host", "0.0.0.0", "--port", "8080"]
