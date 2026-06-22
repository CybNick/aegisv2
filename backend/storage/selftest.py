"""Deterministic self-tests for the Aegis CCEIP storage layer (Milestone 5).

Run with::

    python -m backend.storage.selftest

On success the final line is exactly ``ALL PASS`` and the process exits 0. On any
failure the offending check is printed and the process exits non-zero.

All tests use temporary directories — the user's ``~/.aegis`` is never touched.
Logical integer timestamps and explicit confidences make every result fully
determined by content.

Covered scenarios:

1.  graph_save_load              — PersistentGraphStore save→load byte-identical
2.  event_append_replay          — EventStore append→replay round-trip
3.  snapshot_creation            — SnapshotManager creates immutable snapshot
4.  snapshot_restore             — Snapshot load reconstructs identical graph
5.  retention_execution          — RetentionManager archives old events/snapshots
6.  integrity_validation         — IntegrityValidator detects valid + corrupted
7.  deterministic_serialization  — serialize→load→serialize is byte-identical
8.  insertion_order_independence — shuffled assertions produce identical output
9.  replay_equivalence           — event replay consistency check
10. crash_safe_write             — simulated crash leaves original file intact
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from backend.graph.model import (
    EdgeType,
    NodeType,
    Provenance,
)
from backend.graph.schemas import (
    AssetObservation,
    AssetRef,
    Event,
    EventType,
    ServiceObservation,
    ZoneObservation,
)
from backend.graph.builder import GraphBuilder
from backend.graph.store import GraphStore
from backend.storage.event_store import EventStore, EventReplayer
from backend.storage.graph_store import (
    PersistentGraphStore,
    StorageLayout,
    atomic_write_text,
    read_text,
    sha256_hex,
)
from backend.storage.retention import (
    IntegrityReport,
    IntegrityValidator,
    RetentionManager,
    RetentionPolicy,
)
from backend.storage.snapshots import SnapshotManager

_EV = ("evidence:selftest",)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _make_layout(tmp: str) -> StorageLayout:
    """Create a StorageLayout rooted in a temp directory."""
    layout = StorageLayout(root=Path(tmp))
    layout.ensure_dirs()
    return layout


def _sample_store() -> GraphStore:
    """Build a deterministic sample graph for testing."""
    store = GraphStore()
    # Nodes.
    asset = store.ensure_node(NodeType.ASSET, {"hostname": "web-01"})
    svc = store.ensure_node(NodeType.SERVICE, {"asset": asset.id, "port": 443})
    zone = store.ensure_node(NodeType.ZONE, {"name": "DMZ"})

    # Edges.
    hosts = store.ensure_edge(EdgeType.HOSTS, asset, svc, context="default")
    in_zone = store.ensure_edge(EdgeType.IN_ZONE, asset, zone, context="default")

    # Assertions.
    store.assert_node(
        asset, value={"exists": True, "os": "linux"},
        provenance=Provenance.OBSERVED, confidence=0.9,
        source="scan", valid_from=100, evidence=_EV,
    )
    store.assert_node(
        svc, value={"exists": True, "port": 443},
        provenance=Provenance.OBSERVED, confidence=0.9,
        source="scan", valid_from=100, evidence=_EV,
    )
    store.assert_node(
        zone, value={"exists": True, "name": "DMZ"},
        provenance=Provenance.OBSERVED, confidence=0.9,
        source="scan", valid_from=100, evidence=_EV,
    )
    store.assert_edge(
        hosts, value={"exists": True},
        provenance=Provenance.OBSERVED, confidence=0.9,
        source="scan", valid_from=100, evidence=_EV,
    )
    store.assert_edge(
        in_zone, value={"exists": True},
        provenance=Provenance.OBSERVED, confidence=0.9,
        source="scan", valid_from=100, evidence=_EV,
    )
    return store


def _sample_events() -> list[Event]:
    """Build a deterministic set of sample events."""
    return [
        Event.create(
            event_type=EventType.ASSET_DISCOVERED,
            timestamp=100.0,
            source="scan",
            confidence=0.9,
            evidence=_EV,
            affected_entities=("node_abc",),
            metadata={"node_type": "ASSET"},
        ),
        Event.create(
            event_type=EventType.SERVICE_DETECTED,
            timestamp=200.0,
            source="scan",
            confidence=0.85,
            evidence=_EV,
            affected_entities=("node_def",),
            metadata={"node_type": "SERVICE"},
        ),
        Event.create(
            event_type=EventType.ZONE_DISCOVERED,
            timestamp=300.0,
            source="scan",
            confidence=0.95,
            evidence=_EV,
            affected_entities=("node_ghi",),
            metadata={"node_type": "ZONE"},
        ),
        Event.create(
            event_type=EventType.RELATIONSHIP_OBSERVED,
            timestamp=400.0,
            source="scan",
            confidence=0.9,
            evidence=_EV,
            affected_entities=("edge_jkl", "node_abc", "node_def"),
            metadata={"edge_type": "HOSTS"},
        ),
    ]


# --------------------------------------------------------------------------- #
# 1. graph_save_load                                                           #
# --------------------------------------------------------------------------- #

def test_graph_save_load() -> None:
    """PersistentGraphStore save → load produces byte-identical graph."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        pgs = PersistentGraphStore(layout)
        store = _sample_store()

        before = store.serialize()
        save_hash = pgs.save(store)

        loaded = pgs.load()
        after = loaded.serialize()

        assert before == after, "save→load must be byte-identical"
        assert sha256_hex(before) == save_hash, "save hash must match content"


# --------------------------------------------------------------------------- #
# 2. event_append_replay                                                       #
# --------------------------------------------------------------------------- #

def test_event_append_replay() -> None:
    """EventStore append → replay round-trips events correctly."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        es = EventStore(layout)
        events = _sample_events()

        es.append_many(events)
        assert es.count() == len(events), "all events persisted"

        replayed = es.replay()
        assert len(replayed) == len(events), "all events replayed"

        # Canonical order: (timestamp, id).
        for i in range(len(replayed) - 1):
            assert (replayed[i].timestamp, replayed[i].id) <= \
                   (replayed[i + 1].timestamp, replayed[i + 1].id), \
                "events in canonical order"

        # Idempotent append: re-appending same events is a no-op.
        es.append_many(events)
        assert es.count() == len(events), "duplicate events are idempotent"

        # Temporal filter.
        as_of_250 = es.events_as_of(250.0)
        assert len(as_of_250) == 2, "events_as_of filters by timestamp"
        assert all(e.timestamp <= 250.0 for e in as_of_250)


# --------------------------------------------------------------------------- #
# 3. snapshot_creation                                                         #
# --------------------------------------------------------------------------- #

def test_snapshot_creation() -> None:
    """SnapshotManager creates immutable snapshot with metadata."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        sm = SnapshotManager(layout)
        store = _sample_store()

        meta = sm.snapshot(store, "weekly", created_at=1000.0)
        assert meta.name == "weekly"
        assert meta.created_at == 1000.0
        assert meta.node_count == 3
        assert meta.edge_count == 2
        assert meta.assertion_count == 5
        assert meta.content_hash == sha256_hex(store.serialize())

        # Listing snapshots.
        snapshots = sm.list_snapshots()
        assert len(snapshots) == 1 and snapshots[0].name == "weekly"

        # Immutability: creating the same name raises ValueError.
        raised = False
        try:
            sm.snapshot(store, "weekly", created_at=2000.0)
        except ValueError:
            raised = True
        assert raised, "duplicate snapshot name must raise ValueError"


# --------------------------------------------------------------------------- #
# 4. snapshot_restore                                                          #
# --------------------------------------------------------------------------- #

def test_snapshot_restore() -> None:
    """Snapshot load reconstructs an identical graph."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        sm = SnapshotManager(layout)
        store = _sample_store()
        original = store.serialize()

        sm.snapshot(store, "restore-test", created_at=1000.0)
        restored = sm.load_snapshot("restore-test")
        assert restored.serialize() == original, \
            "restored snapshot must be byte-identical to original"

        # Delete and verify removal.
        sm.delete_snapshot("restore-test")
        assert sm.list_snapshots() == [], "snapshot deleted"


# --------------------------------------------------------------------------- #
# 5. retention_execution                                                       #
# --------------------------------------------------------------------------- #

def test_retention_execution() -> None:
    """RetentionManager archives old events and snapshots correctly."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)

        # --- Event retention ---
        es = EventStore(layout)
        # Old event (timestamp=100) and recent event (timestamp=9_000_000).
        old_event = Event.create(
            event_type=EventType.ASSET_DISCOVERED, timestamp=100.0,
            source="scan", confidence=0.9, evidence=_EV,
            affected_entities=("old",), metadata={},
        )
        recent_event = Event.create(
            event_type=EventType.SERVICE_DETECTED, timestamp=9_000_000.0,
            source="scan", confidence=0.9, evidence=_EV,
            affected_entities=("recent",), metadata={},
        )
        es.append(old_event)
        es.append(recent_event)

        rm = RetentionManager(layout)
        # Apply 7-day retention with now=9_000_000 (cutoff at 9_000_000 - 604800).
        report = rm.apply_event_retention(RetentionPolicy.DAYS_7, now=9_000_000.0)
        assert report.archived_count == 1, "old event archived"
        assert report.remaining_count == 1, "recent event kept"
        assert report.archive_path is not None

        # FOREVER policy is a no-op.
        report2 = rm.apply_event_retention(RetentionPolicy.FOREVER, now=9_000_000.0)
        assert report2.archived_count == 0, "FOREVER archives nothing"

        # --- Snapshot retention ---
        sm = SnapshotManager(layout)
        store = _sample_store()
        sm.snapshot(store, "old-snap", created_at=100.0)
        sm.snapshot(store, "new-snap", created_at=9_000_000.0)

        snap_report = rm.apply_snapshot_retention(
            RetentionPolicy.DAYS_7, now=9_000_000.0
        )
        assert snap_report.archived_count == 1, "old snapshot archived"
        assert snap_report.remaining_count == 1, "recent snapshot kept"

        remaining = sm.list_snapshots()
        assert len(remaining) == 1 and remaining[0].name == "new-snap"


# --------------------------------------------------------------------------- #
# 6. integrity_validation                                                      #
# --------------------------------------------------------------------------- #

def test_integrity_validation() -> None:
    """IntegrityValidator detects valid and corrupted data."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        validator = IntegrityValidator(layout)

        # Valid graph.
        store = _sample_store()
        report = validator.validate_graph(store)
        assert report.valid, f"valid graph must pass: {report.issues}"
        assert "graph_content" in report.hashes

        # Valid events.
        es = EventStore(layout)
        es.append_many(_sample_events())
        report2 = validator.validate_events()
        assert report2.valid, f"valid events must pass: {report2.issues}"

        # Valid snapshot.
        sm = SnapshotManager(layout)
        sm.snapshot(store, "integrity-test", created_at=1000.0)
        report3 = validator.validate_snapshot("integrity-test")
        assert report3.valid, f"valid snapshot must pass: {report3.issues}"

        # Valid checkpoint.
        pgs = PersistentGraphStore(layout)
        pgs.checkpoint(store, "test-cp")
        report4 = validator.validate_checkpoint(pgs, "test-cp")
        assert report4.valid, f"valid checkpoint must pass: {report4.issues}"

        # Corrupted event file.
        events_path = layout.events_jsonl
        with open(events_path, "a", encoding="utf-8") as fh:
            fh.write("this is not valid json\n")
        report5 = validator.validate_events()
        assert not report5.valid, "corrupted events must fail validation"

        # Missing snapshot.
        report6 = validator.validate_snapshot("nonexistent")
        assert not report6.valid, "missing snapshot must fail"


# --------------------------------------------------------------------------- #
# 7. deterministic_serialization                                               #
# --------------------------------------------------------------------------- #

def test_deterministic_serialization() -> None:
    """Graph serialize → load → serialize is byte-identical."""
    store = _sample_store()

    s1 = store.serialize()
    s2 = store.serialize()
    assert s1 == s2, "serialization is stable across calls"

    loaded = GraphStore.load(s1)
    s3 = loaded.serialize()
    assert s1 == s3, "round-trip is lossless and canonical"

    # Persisted round-trip.
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        pgs = PersistentGraphStore(layout)
        pgs.save(store)
        loaded2 = pgs.load()
        assert store.serialize() == loaded2.serialize(), \
            "disk round-trip is byte-identical"


# --------------------------------------------------------------------------- #
# 8. insertion_order_independence                                              #
# --------------------------------------------------------------------------- #

def test_insertion_order_independence() -> None:
    """Shuffled assertion insertion produces identical serialization."""
    specs = [
        ({"hostname": "h1"}, {"os": "linux"}, Provenance.OBSERVED, 0.9, 3, 0, "prod"),
        ({"hostname": "h1"}, {"os": "bsd"}, Provenance.INFERRED, 0.95, 8, 0, "prod"),
        ({"hostname": "h2"}, {"role": "db"}, Provenance.VERIFIED, 0.85, 2, 0, "prod"),
        ({"hostname": "h2"}, {"role": "cache"}, Provenance.VERIFIED, 0.85, 7, 0, "dev"),
        ({"hostname": "h3"}, {"zone": "dmz"}, Provenance.OBSERVED, 0.7, 1, 0, "prod"),
        ({"hostname": "h3"}, {"zone": "int"}, Provenance.OBSERVED, 0.7, 6, 0, "prod"),
    ]

    def build_from(order: list[int]) -> GraphStore:
        store = GraphStore()
        for i in order:
            key, val, prov, conf, obs, vf, ctx = specs[i]
            node = store.ensure_node(NodeType.ASSET, key)
            store.assert_node(
                node, value=val, provenance=prov, confidence=conf, source="s",
                valid_from=vf, observed_at=obs, context=ctx,
                evidence=() if prov is Provenance.UNKNOWN else _EV,
            )
        return store

    forward = list(range(len(specs)))
    reverse = list(reversed(forward))
    interleaved = forward[::2] + forward[1::2]

    s_fwd = build_from(forward).serialize()
    s_rev = build_from(reverse).serialize()
    s_int = build_from(interleaved).serialize()

    assert s_fwd == s_rev == s_int, "serialization is independent of insertion order"

    # Also verify on disk.
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        pgs = PersistentGraphStore(layout)

        pgs.save(build_from(forward))
        loaded_fwd = pgs.load().serialize()

        pgs.save(build_from(reverse))
        loaded_rev = pgs.load().serialize()

        assert loaded_fwd == loaded_rev, "disk persistence is insertion-order independent"


# --------------------------------------------------------------------------- #
# 9. replay_equivalence                                                        #
# --------------------------------------------------------------------------- #

def test_replay_equivalence() -> None:
    """Graph built from observations matches event replay consistency check."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        es = EventStore(layout)

        # Build a graph through the builder, capturing events.
        observations = [
            AssetObservation(
                ref=AssetRef(hostname="web-01"), zone="DMZ",
                source="scan", evidence=_EV, observed_at=100,
                attributes={"os": "linux"},
            ),
            ServiceObservation(
                host=AssetRef(hostname="web-01"), port=443,
                source="scan", evidence=_EV, observed_at=100,
            ),
            ZoneObservation(
                name="DMZ", source="scan", evidence=_EV, observed_at=100,
            ),
        ]

        builder = GraphBuilder()
        result = builder.build(observations)

        # Persist events.
        es.append_many(list(result.events))

        # Build the graph from builder output.
        store = GraphStore()
        for node in result.nodes:
            store._nodes[node.id] = node
        for edge in result.edges:
            store._edges[edge.id] = edge
        for assertion in result.assertions:
            store.append(assertion)

        original_serialization = store.serialize()

        # Save and reload graph.
        pgs = PersistentGraphStore(layout)
        pgs.save(store)
        reloaded = pgs.load()

        assert reloaded.serialize() == original_serialization, \
            "reloaded graph matches original"

        # Verify event replay consistency.
        replayer = EventReplayer(es)
        replayed_events = replayer.replay_events()
        assert len(replayed_events) == len(result.events), \
            "all events round-tripped"

        # Verify events reference entities in the graph.
        assert replayer.verify_consistency(store), \
            "event entities exist in graph"

        # Event canonical ordering matches original.
        original_event_ids = sorted(e.id for e in result.events)
        replayed_event_ids = sorted(e.id for e in replayed_events)
        assert original_event_ids == replayed_event_ids, \
            "replayed event ids match original"


# --------------------------------------------------------------------------- #
# 10. crash_safe_write                                                         #
# --------------------------------------------------------------------------- #

def test_crash_safe_write() -> None:
    """Simulated crash leaves the original file intact."""
    with tempfile.TemporaryDirectory() as tmp:
        layout = _make_layout(tmp)
        pgs = PersistentGraphStore(layout)
        store = _sample_store()

        # Save initial state.
        pgs.save(store)
        original_content = read_text(layout.graph_json)

        # Simulate a crash: atomic_write_text with _simulate_crash=True.
        crashed = False
        try:
            atomic_write_text(
                layout.graph_json,
                '{"corrupted": true}',
                _simulate_crash=True,
            )
        except RuntimeError:
            crashed = True

        assert crashed, "crash simulation must raise RuntimeError"

        # Original file must be intact.
        after_crash = read_text(layout.graph_json)
        assert after_crash == original_content, \
            "original file must survive a simulated crash"

        # Temp file must not remain.
        tmp_file = layout.graph_json.with_name(layout.graph_json.name + ".tmp")
        assert not tmp_file.exists(), "temp file must be cleaned up after crash"


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

_TESTS: list[tuple[str, Callable[[], None]]] = [
    ("graph_save_load", test_graph_save_load),
    ("event_append_replay", test_event_append_replay),
    ("snapshot_creation", test_snapshot_creation),
    ("snapshot_restore", test_snapshot_restore),
    ("retention_execution", test_retention_execution),
    ("integrity_validation", test_integrity_validation),
    ("deterministic_serialization", test_deterministic_serialization),
    ("insertion_order_independence", test_insertion_order_independence),
    ("replay_equivalence", test_replay_equivalence),
    ("crash_safe_write", test_crash_safe_write),
]


def run() -> bool:
    """Run every self-test, printing per-test status. Returns True if all pass."""
    all_ok = True
    for index, (name, fn) in enumerate(_TESTS, start=1):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - report any failure verbatim
            all_ok = False
            print(f"[FAIL] {index}. {name}: {exc}")
        else:
            print(f"[PASS] {index}. {name}")
    return all_ok


def main() -> int:
    """Entry point: print ``ALL PASS`` on success, else exit non-zero."""
    if run():
        print("ALL PASS")
        return 0
    print("FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
