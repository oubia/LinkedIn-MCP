import logging
import os
from typing import Any, Dict


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_json(logger: logging.Logger, level: int, message: str, extra: Dict[str, Any] | None = None) -> None:
    payload = {"message": message}
    if extra:
        payload.update(extra)
    logger.log(level, "%s", payload)
