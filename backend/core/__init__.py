"""Core layer — shared configuration, logging, and primitives.

This package holds cross-cutting concerns used by every other layer:
configuration (:mod:`backend.core.config`) and logging
(:mod:`backend.core.logging`). It carries no domain logic and must not depend
on any other backend layer.
"""

from .config import Settings, get_settings
from .logging import configure_logging, get_logger

__all__ = [
    "Settings",
    "get_settings",
    "configure_logging",
    "get_logger",
]
