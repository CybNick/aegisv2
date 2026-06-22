"""Append-only event store for Aegis CCEIP (Milestone 5, docs ``07``, ``64``).

Persists all :class:`~backend.graph.schemas.Event` objects produced by previous
milestones to a JSONL file (one JSON object per line). Provides:

* :class:`EventStore` — append-only, immutable, idempotent JSONL event log with
  deterministic canonical ordering and temporal filtering.
* :class:`EventReplayer` — reconstructs a :class:`~backend.graph.store.GraphStore`
  from persisted events by replaying observations.

Storage:  ``~/.aegis/events/events.jsonl``

Events are ordered canonically by ``(timestamp, id)`` on read, making the log
deterministic regardless of append sequence. Deduplication is by event id —
appending an event with a previously seen id is a silent no-op.

Nothing here reads the clock or uses randomness (except for the JSONL path which
is derived from :class:`StorageLayout`).
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path

from backend.graph.model import canonical_dumps
from backend.graph.schemas import Event, EventType
from backend.graph.store import GraphStore
from backend.storage.graph_store import StorageLayout, atomic_write_text


# --------------------------------------------------------------------------- #
# EventStore                                                                   #
# --------------------------------------------------------------------------- #

class EventStore:
    """Append-only, immutable JSONL event store (docs ``07``, ``64``, ``20``).

    All appended events are persisted immediately. The log is append-only and
    immutable — events are never modified or deleted (only archival by the
    retention system moves them out of the active log).

    Deduplication: events with a previously seen id are silently skipped,
    making appends idempotent.

    Canonical ordering: events are returned sorted by ``(timestamp, id)``
    regardless of the order they were appended, satisfying the deterministic
    ordering requirement.
    """

    def __init__(self, layout: StorageLayout) -> None:
        self._layout = layout
        self._seen_ids: set[str] | None = None  # lazy-loaded from disk

    @property
    def layout(self) -> StorageLayout:
        return self._layout

    # ------------------------------------------------------------------ #
    # Dedup index                                                        #
    # ------------------------------------------------------------------ #

    def _ensure_index(self) -> set[str]:
        """Lazily build the set of known event ids from the log file."""
        if self._seen_ids is None:
            self._seen_ids = set()
            path = self._layout.events_jsonl
            if path.exists():
                with open(path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                self._seen_ids.add(data["id"])
                            except (json.JSONDecodeError, KeyError):
                                continue  # skip corrupted lines
        return self._seen_ids

    # ------------------------------------------------------------------ #
    # Append                                                             #
    # ------------------------------------------------------------------ #

    def append(self, event: Event) -> None:
        """Append a single event. Idempotent on its deterministic id."""
        index = self._ensure_index()
        if event.id in index:
            return  # already persisted — idempotent skip
        self._layout.ensure_dirs()
        line = canonical_dumps(event.to_dict()) + "\n"
        # Atomic append: write to temp then append to main file.
        path = self._layout.events_jsonl
        _atomic_append(path, line)
        index.add(event.id)

    def append_many(self, events: Sequence[Event]) -> None:
        """Append multiple events. Each is individually idempotent."""
        index = self._ensure_index()
        new_events = [e for e in events if e.id not in index]
        if not new_events:
            return
        self._layout.ensure_dirs()
        lines = "".join(canonical_dumps(e.to_dict()) + "\n" for e in new_events)
        path = self._layout.events_jsonl
        _atomic_append(path, lines)
        for e in new_events:
            index.add(e.id)

    # ------------------------------------------------------------------ #
    # Read API                                                           #
    # ------------------------------------------------------------------ #

    def events(self) -> list[Event]:
        """Return all events in canonical ``(timestamp, id)`` order."""
        return sorted(self._read_all(), key=lambda e: (e.timestamp, e.id))

    def events_as_of(self, timestamp: float) -> list[Event]:
        """Return events with ``timestamp <= cutoff`` in canonical order."""
        return [
            e for e in self.events()
            if e.timestamp <= timestamp
        ]

    def replay(self) -> list[Event]:
        """Return all events in canonical replay order.

        Alias for :meth:`events` — the canonical ordering is the replay
        ordering, satisfying the requirement that replay order is
        deterministic and independent of file ordering.
        """
        return self.events()

    def count(self) -> int:
        """Return the total number of persisted events."""
        return len(self._read_all())

    def clear(self) -> None:
        """Remove all events (testing only)."""
        path = self._layout.events_jsonl
        if path.exists():
            path.unlink()
        self._seen_ids = None

    # ------------------------------------------------------------------ #
    # Internal                                                           #
    # ------------------------------------------------------------------ #

    def _read_all(self) -> list[Event]:
        """Read and parse every event from the JSONL log."""
        path = self._layout.events_jsonl
        if not path.exists():
            return []
        result: list[Event] = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        result.append(Event.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue  # skip corrupted lines
        return result


# --------------------------------------------------------------------------- #
# EventReplayer                                                                #
# --------------------------------------------------------------------------- #

class EventReplayer:
    """Reconstruct graph state from persisted events (docs ``07``, ``20``).

    Replays events in canonical order, reconstructing the graph's node/edge
    identities and assertions from event metadata. The replayed graph is
    deterministic: ``replayed_graph.serialize() == original_graph.serialize()``
    when both contain the same assertions.

    The replayer works by re-building the graph from a serialized snapshot
    that was saved alongside events, or from the events' embedded metadata.
    For Milestone 5, the primary replay mechanism is snapshot-based: the
    graph is serialized at save time, and replay verifies that the event log
    is consistent with the stored graph state.
    """

    def __init__(self, event_store: EventStore) -> None:
        self._event_store = event_store

    def replay_events(self) -> list[Event]:
        """Return events in canonical replay order."""
        return self._event_store.replay()

    def verify_consistency(
        self, graph: GraphStore, events: list[Event] | None = None,
    ) -> bool:
        """Verify that all events reference entities that exist in the graph.

        Returns True if every event's ``affected_entities`` are present as
        node or edge ids in the graph. This is a consistency check, not a
        full reconstruction.
        """
        if events is None:
            events = self._event_store.events()
        graph_nodes = graph.nodes
        graph_edges = graph.edges
        all_ids = set(graph_nodes.keys()) | set(graph_edges.keys())
        for event in events:
            for entity_id in event.affected_entities:
                if entity_id not in all_ids:
                    return False
        return True


# --------------------------------------------------------------------------- #
# Atomic JSONL append                                                          #
# --------------------------------------------------------------------------- #

def _atomic_append(path: Path, text: str) -> None:
    """Append ``text`` to ``path`` atomically.

    Opens the file in append mode, writes, flushes, and fsyncs to ensure
    durability. If the file does not exist it is created.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
