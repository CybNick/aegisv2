"""Immutable snapshot system for Aegis CCEIP (Milestone 5, docs ``20``, ``62``).

Provides :class:`SnapshotManager` — create, load, list, and delete named graph
snapshots. Each snapshot is an immutable, timestamped copy of the full
:class:`~backend.graph.store.GraphStore` state, stored under:

    ``~/.aegis/graph/snapshots/<name>/``
        ├── ``graph.json``     — canonical graph serialization
        └── ``metadata.json``  — snapshot metadata (name, hash, counts, etc.)

Snapshots are immutable: creating a snapshot with an already-existing name
raises ``ValueError``. Deletion is explicit. Atomic writes ensure crash safety.

Nothing here reads the wall clock or uses randomness — all timestamps are
caller-supplied.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.graph.model import SCHEMA_VERSION, canonical_dumps
from backend.graph.store import GraphStore
from backend.storage.graph_store import (
    StorageLayout,
    atomic_write_text,
    read_text,
    sha256_hex,
)


# --------------------------------------------------------------------------- #
# Snapshot metadata                                                            #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class SnapshotMetadata:
    """Metadata for an immutable graph snapshot.

    All fields are JSON-safe so the metadata can be persisted alongside the
    graph content.
    """

    name: str
    created_at: float
    content_hash: str
    schema_version: int
    node_count: int
    edge_count: int
    assertion_count: int

    def to_dict(self) -> dict[str, Any]:
        """Return a canonical, JSON-safe representation."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "content_hash": self.content_hash,
            "schema_version": self.schema_version,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "assertion_count": self.assertion_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SnapshotMetadata":
        """Reconstruct metadata from :meth:`to_dict` output."""
        return cls(
            name=data["name"],
            created_at=data["created_at"],
            content_hash=data["content_hash"],
            schema_version=data["schema_version"],
            node_count=data["node_count"],
            edge_count=data["edge_count"],
            assertion_count=data["assertion_count"],
        )


# --------------------------------------------------------------------------- #
# SnapshotManager                                                              #
# --------------------------------------------------------------------------- #

class SnapshotManager:
    """Immutable, timestamped graph snapshot manager (docs ``20``, ``62``, ``63``).

    Snapshots are the primary mechanism for historical graph reconstruction:
    ``snapshot("weekly")`` preserves a full graph copy that can be loaded at
    any time. Combined with the event store, they support AS-OF analysis,
    drift detection, and change reporting.
    """

    def __init__(self, layout: StorageLayout) -> None:
        self._layout = layout

    @property
    def layout(self) -> StorageLayout:
        return self._layout

    # ------------------------------------------------------------------ #
    # Create                                                             #
    # ------------------------------------------------------------------ #

    def snapshot(
        self,
        store: GraphStore,
        name: str,
        *,
        created_at: float = 0.0,
    ) -> SnapshotMetadata:
        """Create a named, immutable snapshot of ``store``.

        Args:
            store: The graph store to snapshot.
            name: Unique snapshot name (e.g. ``"weekly"``, ``"daily"``).
            created_at: Logical timestamp for the snapshot. Defaults to ``0.0``
                (tests use explicit timestamps; production callers supply
                wall-clock time).

        Raises:
            ValueError: if a snapshot with ``name`` already exists.

        Returns:
            The snapshot metadata.
        """
        snap_dir = self._snapshot_dir(name)
        if snap_dir.exists():
            raise ValueError(f"Snapshot {name!r} already exists at {snap_dir}")

        self._layout.ensure_dirs()
        snap_dir.mkdir(parents=True, exist_ok=True)

        # Write the canonical graph.
        text = store.serialize()
        content_hash = sha256_hex(text)
        atomic_write_text(snap_dir / "graph.json", text)

        # Compute counts from the store's to_dict() output.
        store_dict = store.to_dict()
        meta = SnapshotMetadata(
            name=name,
            created_at=created_at,
            content_hash=content_hash,
            schema_version=store_dict.get("schema_version", SCHEMA_VERSION),
            node_count=len(store_dict.get("nodes", [])),
            edge_count=len(store_dict.get("edges", [])),
            assertion_count=len(store_dict.get("assertions", [])),
        )
        atomic_write_text(
            snap_dir / "metadata.json",
            canonical_dumps(meta.to_dict()),
        )
        return meta

    # ------------------------------------------------------------------ #
    # Load                                                               #
    # ------------------------------------------------------------------ #

    def load_snapshot(self, name: str) -> GraphStore:
        """Load a snapshot by name.

        Raises:
            FileNotFoundError: if no snapshot with ``name`` exists.
        """
        graph_path = self._snapshot_dir(name) / "graph.json"
        if not graph_path.exists():
            raise FileNotFoundError(f"No snapshot {name!r} at {graph_path}")
        return GraphStore.load(read_text(graph_path))

    # ------------------------------------------------------------------ #
    # List / metadata                                                    #
    # ------------------------------------------------------------------ #

    def list_snapshots(self) -> list[SnapshotMetadata]:
        """Return metadata for all snapshots, sorted by name."""
        base = self._layout.snapshots_dir
        if not base.exists():
            return []
        result: list[SnapshotMetadata] = []
        for child in sorted(base.iterdir()):
            meta_path = child / "metadata.json"
            if child.is_dir() and meta_path.exists():
                # Skip the archive subdirectory.
                if child.name == "archive":
                    continue
                try:
                    data = json.loads(read_text(meta_path))
                    result.append(SnapshotMetadata.from_dict(data))
                except (json.JSONDecodeError, KeyError):
                    continue  # skip corrupted metadata
        return result

    def get_metadata(self, name: str) -> SnapshotMetadata:
        """Return the metadata for a named snapshot.

        Raises:
            FileNotFoundError: if no snapshot with ``name`` exists.
        """
        meta_path = self._snapshot_dir(name) / "metadata.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"No snapshot metadata for {name!r}")
        data = json.loads(read_text(meta_path))
        return SnapshotMetadata.from_dict(data)

    # ------------------------------------------------------------------ #
    # Delete                                                             #
    # ------------------------------------------------------------------ #

    def delete_snapshot(self, name: str) -> None:
        """Delete a snapshot by name.

        Raises:
            FileNotFoundError: if no snapshot with ``name`` exists.
        """
        snap_dir = self._snapshot_dir(name)
        if not snap_dir.exists():
            raise FileNotFoundError(f"No snapshot {name!r} at {snap_dir}")
        # Remove all files in the snapshot directory.
        for f in snap_dir.iterdir():
            f.unlink()
        snap_dir.rmdir()

    # ------------------------------------------------------------------ #
    # Internal                                                           #
    # ------------------------------------------------------------------ #

    def _snapshot_dir(self, name: str) -> Path:
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise ValueError(f"Invalid snapshot name: {name!r}")
        return self._layout.snapshots_dir / name
