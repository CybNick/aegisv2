"""Storage layer for Aegis CCEIP (Milestone 5, docs ``20``, ``62``, ``64``, ``67``).

Local-first, append-only, JSON-only persistence. Provides:

* :class:`StorageLayout` — the on-disk ``~/.aegis`` directory layout.
* :class:`PersistentGraphStore` — save/load/checkpoint/restore for the graph.
* :class:`EventStore` — append-only, immutable JSONL event log.
* :class:`EventReplayer` — reconstruct graph state from persisted events.
* :class:`SnapshotManager` — immutable, timestamped graph snapshots.
* :class:`RetentionManager` — policy-based archival of events and snapshots.
* :class:`IntegrityValidator` — hash and round-trip validation across all tiers.

No databases, no cloud, no external dependencies — JSON / JSONL only.
"""

from backend.storage.event_store import EventReplayer, EventStore
from backend.storage.graph_store import (
    PersistentGraphStore,
    StorageLayout,
    atomic_write_text,
    sha256_hex,
)
from backend.storage.retention import (
    IntegrityReport,
    IntegrityValidator,
    RetentionManager,
    RetentionPolicy,
    RetentionReport,
)
from backend.storage.snapshots import SnapshotManager, SnapshotMetadata

__all__ = [
    "StorageLayout",
    "PersistentGraphStore",
    "EventStore",
    "EventReplayer",
    "SnapshotManager",
    "SnapshotMetadata",
    "RetentionManager",
    "RetentionPolicy",
    "RetentionReport",
    "IntegrityValidator",
    "IntegrityReport",
    "atomic_write_text",
    "sha256_hex",
]
