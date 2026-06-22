"""Application configuration for Aegis CCEIP.

Configuration is **local-first** and **deterministic**: every value has a safe
default that works on a single workstation with no cloud dependencies, and any
value may be overridden through an ``AEGIS_``-prefixed environment variable.

No secrets are stored in this module (engineering standard ``99``). Version 1 of
the platform is local-only and single-user (``21``).

Environment overrides
----------------------
========================  =======================================  ===========
Environment variable      Setting                                   Default
========================  =======================================  ===========
``AEGIS_HOST``            :attr:`Settings.host`                     ``127.0.0.1``
``AEGIS_PORT``            :attr:`Settings.port`                     ``8000``
``AEGIS_LOG_LEVEL``       :attr:`Settings.log_level`                ``INFO``
``AEGIS_DATA_DIR``        :attr:`Settings.data_dir`                 ``~/.aegis``
``AEGIS_RELOAD``          :attr:`Settings.reload`                   ``false``
``AEGIS_AUTH_ENABLED``    :attr:`Settings.auth_enabled`             ``false``
``AEGIS_SEED_DEMO``       :attr:`Settings.seed_demo`                ``false``
========================  =======================================  ===========
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from backend import __app_name__, __app_title__, __version__

# Local-first persistence layout (see Storage Architecture, doc ``20``).
# These subdirectories live under :attr:`Settings.data_dir` (default ``~/.aegis``).
_STORE_SUBDIRS: tuple[str, ...] = (
    "graph",
    "events",
    "evidence",
    "reports",
    "exports",
    "logs",
)

_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_str(name: str, default: str) -> str:
    """Return an environment override, falling back to ``default``."""
    value = os.environ.get(name)
    return value if value is not None and value != "" else default


def _env_int(name: str, default: int) -> int:
    """Return an integer environment override, falling back to ``default``."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _env_bool(name: str, default: bool) -> bool:
    """Return a boolean environment override, falling back to ``default``."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in _TRUE_VALUES


@dataclass(frozen=True)
class Settings:
    """Immutable, fully-resolved application settings.

    The instance is frozen so configuration cannot drift at runtime, supporting
    the platform's determinism guarantee (``06``).
    """

    app_name: str = __app_name__
    app_title: str = __app_title__
    version: str = __version__

    host: str = field(default_factory=lambda: _env_str("AEGIS_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: _env_int("AEGIS_PORT", 8000))
    log_level: str = field(
        default_factory=lambda: _env_str("AEGIS_LOG_LEVEL", "INFO").upper()
    )
    reload: bool = field(default_factory=lambda: _env_bool("AEGIS_RELOAD", False))

    # Authentication is OFF by default: v1 is local-first and single-user, bound
    # to loopback (``host`` default ``127.0.0.1``), so the bundled SPA can call the
    # API with no key. Set ``AEGIS_AUTH_ENABLED=true`` for any networked deployment
    # to enforce the API-key roles defined in ``backend.api.security``.
    auth_enabled: bool = field(
        default_factory=lambda: _env_bool("AEGIS_AUTH_ENABLED", False)
    )

    # Demo seeding is OFF by default: a brand-new install starts with an empty
    # graph so the first network scan produces the only data the user sees (no
    # fabricated assets). Set ``AEGIS_SEED_DEMO=true`` to load the mock-demo
    # dataset for evaluation/screenshots.
    seed_demo: bool = field(
        default_factory=lambda: _env_bool("AEGIS_SEED_DEMO", False)
    )

    data_dir: Path = field(
        default_factory=lambda: Path(
            _env_str("AEGIS_DATA_DIR", str(Path.home() / ".aegis"))
        ).expanduser()
    )

    @property
    def store_paths(self) -> dict[str, Path]:
        """Map each local store name to its absolute path under :attr:`data_dir`."""
        return {name: self.data_dir / name for name in _STORE_SUBDIRS}

    def ensure_data_dirs(self) -> None:
        """Create the local-first persistence directories if they do not exist.

        This is safe to call repeatedly and never deletes or overwrites data,
        honouring the append-only principle (``20``).
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        for path in self.store_paths.values():
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached, process-wide :class:`Settings` instance."""
    return Settings()
