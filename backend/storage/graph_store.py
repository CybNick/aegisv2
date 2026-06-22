"""Persistent graph storage for Aegis CCEIP (Milestone 5, docs ``20``, ``62``).

Local-first, append-only, JSON-only persistence. Provides:

* :class:`StorageLayout` — the on-disk ``~/.aegis`` directory layout (doc ``20``).
* atomic, crash-safe file primitives (:func:`atomic_write_text`).
* :class:`PersistentGraphStore` — save/load/checkpoint/restore for a
  :class:`~backend.graph.store.GraphStore`.

Serialization reuses the kernel's canonical form, so a save followed by a load is
byte-identical (``serialize(before) == serialize(after_load)``). No databases, no
cloud, no external dependencies — JSON only.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from backend.graph.store import GraphStore


# --------------------------------------------------------------------------- #
# Hashing                                                                      #
# --------------------------------------------------------------------------- #

def sha256_hex(text: str) -> str:
    """Return the SHA-256 hex digest of ``text`` (utf-8)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Atomic, crash-safe file IO                                                   #
# --------------------------------------------------------------------------- #

def atomic_write_text(path: Path, text: str, *, _simulate_crash: bool = False) -> None:
    """Write ``text`` to ``path`` atomically and durably.

    Writes to a sibling ``*.tmp`` file (flushed + fsynced) and then
    :func:`os.replace` swaps it into place — an atomic operation on a single
    filesystem. If anything fails before the swap, the original file is left
    untouched and the temp file is removed, so a crash never yields a partially
    written graph.

    Args:
        path: Destination file.
        text: Content to write.
        _simulate_crash: Test hook — raise after writing the temp file but before
            the atomic swap, to verify crash safety.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if _simulate_crash:
            raise RuntimeError("simulated crash before atomic swap")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def read_text(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Storage layout (doc 20)                                                      #
# --------------------------------------------------------------------------- #

class StorageLayout:
    """The on-disk ``~/.aegis`` directory layout (doc ``20``).

    All paths derive from a single root, so the entire store is portable and
    local-first. A non-default root (e.g. a temp directory) makes the layout
    fully testable without touching the user's home directory.
    """

    def __init__(self, root: Path | str | None = None) -> None:
        if root is None:
            from backend.core.config import get_settings

            root = get_settings().data_dir
        self.root = Path(root).expanduser()

    # graph/
    @property
    def graph_dir(self) -> Path:
        return self.root / "graph"

    @property
    def graph_json(self) -> Path:
        return self.graph_dir / "graph.json"

    @property
    def snapshots_dir(self) -> Path:
        return self.graph_dir / "snapshots"

    @property
    def snapshots_archive_dir(self) -> Path:
        return self.snapshots_dir / "archive"

    @property
    def checkpoints_dir(self) -> Path:
        return self.graph_dir / "checkpoints"

    # events/
    @property
    def events_dir(self) -> Path:
        return self.root / "events"

    @property
    def events_jsonl(self) -> Path:
        return self.events_dir / "events.jsonl"

    @property
    def events_archive_dir(self) -> Path:
        return self.events_dir / "archive"

    # other tiers
    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    @property
    def exports_dir(self) -> Path:
        return self.root / "exports"

    def ensure_dirs(self) -> None:
        """Create the full local-first directory layout (idempotent)."""
        for path in (
            self.graph_dir,
            self.snapshots_dir,
            self.snapshots_archive_dir,
            self.checkpoints_dir,
            self.events_dir,
            self.events_archive_dir,
            self.logs_dir,
            self.reports_dir,
            self.exports_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Persistent graph store                                                       #
# --------------------------------------------------------------------------- #

class PersistentGraphStore:
    """Durable save/load for a :class:`GraphStore` (docs ``20``, ``62``)."""

    def __init__(self, layout: StorageLayout) -> None:
        self._layout = layout

    @property
    def layout(self) -> StorageLayout:
        return self._layout

    def exists(self) -> bool:
        """Whether a persisted graph is present."""
        return self._layout.graph_json.exists()

    def save(self, store: GraphStore) -> str:
        """Persist ``store`` to ``graph/graph.json`` atomically.

        Returns the SHA-256 of the written canonical content.
        """
        self._layout.ensure_dirs()
        text = store.serialize()
        atomic_write_text(self._layout.graph_json, text)
        return sha256_hex(text)

    def load(self) -> GraphStore:
        """Load the persisted graph. Byte-identical to the saved state."""
        if not self.exists():
            raise FileNotFoundError(f"No graph at {self._layout.graph_json}")
        return GraphStore.load(read_text(self._layout.graph_json))

    def load_graph(self) -> GraphStore:
        """Load the persisted graph, returning an empty store if none exists.

        Read-path services call this on every request; on a brand-new install
        (before the first save/seed) there is no graph file yet, so returning an
        empty :class:`GraphStore` keeps those endpoints functional instead of
        raising ``FileNotFoundError``.
        """
        if not self.exists():
            return GraphStore()
        return GraphStore.load(read_text(self._layout.graph_json))

    def checkpoint(self, store: GraphStore, name: str = "latest") -> str:
        """Write a named checkpoint copy of the graph atomically.

        Returns the checkpoint content hash.
        """
        self._layout.ensure_dirs()
        text = store.serialize()
        atomic_write_text(self._checkpoint_path(name), text)
        return sha256_hex(text)

    def restore(self, name: str = "latest") -> GraphStore:
        """Restore a :class:`GraphStore` from a named checkpoint."""
        path = self._checkpoint_path(name)
        if not path.exists():
            raise FileNotFoundError(f"No checkpoint {name!r} at {path}")
        return GraphStore.load(read_text(path))

    def list_checkpoints(self) -> list[str]:
        """Return checkpoint names, sorted."""
        directory = self._layout.checkpoints_dir
        if not directory.exists():
            return []
        return sorted(p.stem for p in directory.glob("*.json"))

    def _checkpoint_path(self, name: str) -> Path:
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise ValueError(f"Invalid checkpoint name: {name!r}")
        return self._layout.checkpoints_dir / f"{name}.json"
