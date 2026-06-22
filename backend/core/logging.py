"""Logging configuration for Aegis CCEIP.

Provides a single, consistent logging setup for the whole application. Logging
is configured once at startup via :func:`configure_logging`; individual modules
obtain a namespaced logger via :func:`get_logger`.

The format is deterministic and human-readable, in keeping with the platform's
explainability and auditability principles.
"""

from __future__ import annotations

import logging

from .config import Settings, get_settings

_LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# Root namespace for all Aegis loggers.
_ROOT_LOGGER_NAME = "aegis"

_configured = False


def configure_logging(settings: Settings | None = None) -> None:
    """Configure the ``aegis`` logger hierarchy.

    Idempotent: calling this more than once does not add duplicate handlers.

    Args:
        settings: Optional settings to use. Defaults to :func:`get_settings`.
    """
    global _configured
    if _configured:
        return

    settings = settings or get_settings()

    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    logger.setLevel(settings.log_level)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))
    logger.addHandler(handler)

    # Avoid double logging through the Python root logger.
    logger.propagate = False

    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger under the ``aegis`` namespace.

    Args:
        name: Optional dotted suffix (e.g. ``"api"``). When omitted, the root
            ``aegis`` logger is returned.

    Returns:
        A configured :class:`logging.Logger`.
    """
    if not name:
        return logging.getLogger(_ROOT_LOGGER_NAME)
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
