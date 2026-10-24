"""Log in JSON su stdout e, se c'è `OTEL_EXPORTER_OTLP_ENDPOINT`, anche al collector di
Solvo (OTLP/HTTP), con le label `service` ed `env` che Loki indicizza: così il Log
investigator e il Problem spotter li trovano con `{service="presenze", env="prod"}`.
Le eccezioni finiscono nel campo `exception` con lo stack trace intero."""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from datetime import UTC, datetime

from presenze import VERSION

SERVICE = os.environ.get("PRESENZE_SERVICE", "presenze")
ENV = os.environ.get("PRESENZE_ENV", "dev")
_providers: list = []


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        line = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "version": VERSION,
        }
        line.update(getattr(record, "fields", {}))
        if record.exc_info:
            line["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(line, ensure_ascii=False, default=str)


def _otlp_handler(endpoint: str) -> logging.Handler:
    from opentelemetry._logs import SeverityNumber
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

    provider = LoggerProvider(
        resource=Resource.create(
            {"service.name": SERVICE, "service": SERVICE, "env": ENV, "service.version": VERSION}
        )
    )
    _providers.append(provider)
    provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{endpoint.rstrip('/')}/v1/logs"))
    )
    otel = provider.get_logger(SERVICE)
    severity = {
        "DEBUG": SeverityNumber.DEBUG,
        "INFO": SeverityNumber.INFO,
        "WARNING": SeverityNumber.WARN,
        "ERROR": SeverityNumber.ERROR,
        "CRITICAL": SeverityNumber.FATAL,
    }

    class Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                otel.emit(
                    timestamp=int(record.created * 1e9),
                    severity_number=severity.get(record.levelname, SeverityNumber.UNSPECIFIED),
                    severity_text={"WARNING": "WARN"}.get(record.levelname, record.levelname),
                    body=self.format(record),
                    attributes={"logger": record.name},
                )
            except Exception:
                self.handleError(record)

    return Handler()


def setup() -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        handlers.append(_otlp_handler(endpoint))
    formatter = JsonFormatter()
    for handler in handlers:
        handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = handlers
    root.setLevel(logging.INFO)
    # Le righe di accesso di uvicorn le scrive già il middleware, con più campi.
    logging.getLogger("uvicorn.access").disabled = True


def shutdown() -> None:
    """Invia le righe ancora in coda (a ogni rilascio il container viene sostituito)."""
    for provider in _providers:
        provider.shutdown()


def log(logger: logging.Logger, level: int, message: str, **fields: object) -> None:
    logger.log(level, message, extra={"fields": fields})
