"""Shared logger for agent modules. Configurable via LOG_LEVEL (debug, info, warn, error)."""
import logging
import os

_LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()
_LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARN": logging.WARNING, "WARNING": logging.WARNING, "ERROR": logging.ERROR}
logging.basicConfig(
    level=_LEVELS.get(_LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
