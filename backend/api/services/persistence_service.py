"""Persistence service for the Aegis CCEIP API (Milestone 6).

A façade over the Milestone 5 storage layer (:mod:`backend.storage`): durable
save/load, named checkpoints, and immutable snapshots of the knowledge graph
(docs ``20``, ``62``). ``graph.json`` under ``~/.aegis`` is the single working
graph; the service re-implements no persistence logic — it delegates to
:class:`PersistentGraphStore` and :class:`SnapshotManager`.

Operational responses (counts, hashes, paths) carry ``confidence = None``: they
describe storage operations, not evidence-backed graph facts.
"""

from __future__ import annotations

import time
from typing import Any

from backend.graph.store import GraphStore
from backend.storage.graph_store import PersistentGraphStore, StorageLayout
from backend.storage.snapshots import SnapshotManager
from backend.api.responses import ApiError
from backend.api.services.graph_service import load_graph

ServiceResult = tuple[Any, float | None, dict[str, Any]]


def _counts(store: GraphStore) -> dict[str, int]:
    """Node / edge / assertion counts for a store (id-sorted, deterministic)."""
    return {
        "nodes": len(store.nodes),
        "edges": len(store.edges),
        "assertions": len(store.assertions),
    }


class PersistenceService:
    """Save / load / checkpoint / snapshot the persisted knowledge graph."""

    def __init__(self, layout: StorageLayout) -> None:
        self._layout = layout
        self._pgs = PersistentGraphStore(layout)
        self._snapshots = SnapshotManager(layout)

    # ------------------------------------------------------------------ #
    # Save / load                                                        #
    # ------------------------------------------------------------------ #

    def save(self) -> ServiceResult:
        """Persist the current working graph atomically (doc ``20``)."""
        store = load_graph(self._layout)
        content_hash = self._pgs.save(store)
        data = {
            "saved": True,
            "hash": content_hash,
            "path": str(self._layout.graph_json),
            "counts": _counts(store),
        }
        return data, None, {}

    def load(self) -> ServiceResult:
        """Load and verify the persisted graph (doc ``62``)."""
        if not self._pgs.exists():
            raise ApiError.not_found(
                f"No persisted graph at {self._layout.graph_json}"
            )
        store = self._pgs.load()
        from backend.storage.graph_store import sha256_hex

        data = {
            "loaded": True,
            "hash": sha256_hex(store.serialize()),
            "counts": _counts(store),
        }
        return data, None, {}

    # ------------------------------------------------------------------ #
    # Checkpoints                                                        #
    # ------------------------------------------------------------------ #

    def checkpoint(self, name: str) -> ServiceResult:
        """Write a named checkpoint of the current working graph."""
        store = load_graph(self._layout)
        content_hash = self._pgs.checkpoint(store, name)
        data = {"checkpoint": name, "hash": content_hash, "counts": _counts(store)}
        return data, None, {}

    def restore(self, name: str) -> ServiceResult:
        """Restore a checkpoint and make it the working graph."""
        try:
            store = self._pgs.restore(name)
        except FileNotFoundError as exc:
            raise ApiError.not_found(f"No checkpoint {name!r}") from exc
        # Restoring promotes the checkpoint to the working graph (doc ``62``).
        self._pgs.save(store)
        data = {"restored": name, "counts": _counts(store)}
        return data, None, {}

    def list_checkpoints(self) -> ServiceResult:
        """List checkpoint names, sorted."""
        names = self._pgs.list_checkpoints()
        return names, None, {"count": len(names)}

    # ------------------------------------------------------------------ #
    # Snapshots                                                          #
    # ------------------------------------------------------------------ #

    def snapshot(self, name: str, *, created_at: float | None = None) -> ServiceResult:
        """Create an immutable, timestamped snapshot of the working graph."""
        store = load_graph(self._layout)
        stamp = created_at if created_at is not None else time.time()
        try:
            meta = self._snapshots.snapshot(store, name, created_at=stamp)
        except ValueError as exc:
            raise ApiError.conflict(f"Snapshot {name!r} already exists") from exc
        return meta.to_dict(), None, {}

    def list_snapshots(self) -> ServiceResult:
        """List snapshot metadata, sorted by name."""
        metas = [m.to_dict() for m in self._snapshots.list_snapshots()]
        return metas, None, {"count": len(metas)}

    def get_snapshot(self, name: str) -> ServiceResult:
        """Return metadata for a named snapshot."""
        try:
            meta = self._snapshots.get_metadata(name)
        except FileNotFoundError as exc:
            raise ApiError.not_found(f"No snapshot {name!r}") from exc
        return meta.to_dict(), None, {}
