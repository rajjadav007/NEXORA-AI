import logging
import re
import sys
from typing import Any


SENSITIVE_PATTERNS = [
    re.compile(r"(password\s*[:=]\s*)([^\s,;&]+)", re.IGNORECASE),
    re.compile(r"(secret\s*[:=]\s*)([^\s,;&]+)", re.IGNORECASE),
    re.compile(r"(token\s*[:=]\s*)([^\s,;&]+)", re.IGNORECASE),
    re.compile(r"(api[-_]?key\s*[:=]\s*)([^\s,;&]+)", re.IGNORECASE),
    re.compile(r"(authorization\s*[:=]\s*Bearer\s+)([^\s,;&]+)", re.IGNORECASE),
]


class RedactingFormatter(logging.Formatter):
    """Sanitize sensitive fields before writing log records."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r"\1[REDACTED]", sanitized)
        return sanitized


def setup_logging(debug: bool = False) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO
    formatter = RedactingFormatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Avoid duplicate handlers on re-init
    root_logger.handlers = [handler]

    logger = logging.getLogger("nexora")
    logger.setLevel(level)
    return logger
