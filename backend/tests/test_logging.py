import logging
from app.core.logging import RedactingFormatter


def test_redacting_formatter_masks_secrets():
    formatter = RedactingFormatter(fmt="%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Login failed with password: supersecret123 and token: eyJhbGciOiJIUzI1NiJ9",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "supersecret123" not in formatted
    assert "eyJhbGciOiJIUzI1NiJ9" not in formatted
    assert "password: [REDACTED]" in formatted
    assert "token: [REDACTED]" in formatted
