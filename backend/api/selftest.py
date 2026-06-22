"""Deterministic self-tests for the Aegis CCEIP API layer (Milestone 6).

Run with::

    python -m backend.api.selftest

On success the final line is exactly ``ALL PASS`` and the process exits 0. On any
failure the offending check is printed and the process exits non-zero.

Every test runs against an isolated temporary ``~/.aegis`` root (injected by
overriding the ``get_storage_layout`` dependency), so the user's real store is
never touched. The graph and events are seeded through the existing Milestone 3
builder and Milestone 5 storage code — the API is exercised only through HTTP via
:class:`fastapi.testclient.TestClient`.

Determinism: every read uses an explicit ``as_of`` and ``context``, so responses
are fully determined by the on-disk graph state (the envelope ``timestamp`` is the
only wall-clock field and is excluded from determinism comparisons).

Covered scenarios (spec order):

1.  health_endpoint              — GET /system/health returns the success envelope
2.  graph_nodes_endpoint         — GET /graph/nodes lists live nodes (+ filter)
3.  graph_view_endpoint          — GET /graph/view returns the resolved view
4.  analysis_risk_endpoint       — GET /analysis/risk returns scored findings
5.  event_replay_endpoint        — GET /events/replay returns canonical order
6.  persistence_save_load        — POST /persistence/save + /load round-trip
7.  checkpoint_restore           — checkpoint then restore the working graph
8.  snapshot_create              — snapshot create + list + get metadata
9.  deterministic_responses      — identical (context, as_of) → identical data
10. insertion_order_independence — shuffled build order → identical API data
"""

from __future__ import annotations

import sys
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

from fastapi.testclient import TestClient

from backend.graph.schemas import (
    AssetObservation,
    AssetRef,
    Observation,
    ServiceObservation,
    ZoneObservation,
)
from backend.graph.builder import GraphBuilder
from backend.graph.store import GraphStore
from backend.storage.event_store import EventStore
from backend.storage.graph_store import PersistentGraphStore, StorageLayout
from backend.api.app import create_app
from backend.api.dependencies import get_storage_layout

_EV = ("evidence:api-selftest",)
_AS_OF = 1000.0
_CTX = "default"


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

def _sample_observations() -> list[Observation]:
    """A deterministic, exposure-bearing observation set.

    A public-zone ("Internet") asset hosting an HTTPS service, with a business
    importance attribute — enough to yield exposure, criticality, and risk
    findings through the existing analyzers.
    """
    return [
        AssetObservation(
            ref=AssetRef(hostname="web-01"),
            zone="Internet",
            source="scan",
            evidence=_EV,
            observed_at=100,
            attributes={"public": True, "business_importance": 0.8},
        ),
        ServiceObservation(
            host=AssetRef(hostname="web-01"),
            port=443,
            source="scan",
            evidence=_EV,
            observed_at=100,
        ),
        ZoneObservation(
            name="Internet", source="scan", evidence=_EV, observed_at=100,
        ),
    ]


def _build_store(observations: Iterable[Observation]) -> tuple[GraphStore, list]:
    """Build a graph store and its events from observations (Milestone 3 builder)."""
    result = GraphBuilder().build(list(observations))
    store = GraphStore()
    for node in result.nodes:
        store._nodes[node.id] = node
    for edge in result.edges:
        store._edges[edge.id] = edge
    for assertion in result.assertions:
        store.append(assertion)
    return store, list(result.events)


def _seed(layout: StorageLayout, *, with_events: bool = True) -> GraphStore:
    """Persist the sample graph (and events) into a temp store, return the store."""
    layout.ensure_dirs()
    store, events = _build_store(_sample_observations())
    PersistentGraphStore(layout).save(store)
    if with_events:
        EventStore(layout).append_many(events)
    return store


def _client(tmp: str) -> TestClient:
    """Build a TestClient whose storage layout is rooted in ``tmp``."""
    layout = StorageLayout(root=Path(tmp))
    layout.ensure_dirs()
    app = create_app()
    app.dependency_overrides[get_storage_layout] = lambda: layout
    return TestClient(app)


def _ok(resp) -> dict:
    """Assert a 200 success envelope and return the parsed body."""
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["success"] is True, f"expected success envelope: {body}"
    assert "timestamp" in body and "data" in body, f"envelope shape: {body}"
    assert "confidence" in body and "metadata" in body, f"envelope shape: {body}"
    return body


# --------------------------------------------------------------------------- #
# 1. health_endpoint                                                           #
# --------------------------------------------------------------------------- #

def test_health_endpoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        client = _client(tmp)
        body = _ok(client.get("/api/v1/system/health"))
        assert body["data"]["status"] == "ok", "health must report ok"


# --------------------------------------------------------------------------- #
# 2. graph_nodes_endpoint                                                      #
# --------------------------------------------------------------------------- #

def test_graph_nodes_endpoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=Path(tmp))
        _seed(layout)
        client = _client(tmp)

        body = _ok(client.get(f"/api/v1/graph/nodes?context={_CTX}&as_of={_AS_OF}"))
        nodes = body["data"]
        assert isinstance(nodes, list) and len(nodes) == 3, f"3 live nodes: {nodes}"
        assert body["metadata"]["total"] == 3, "metadata reports total"
        # Deterministic id-sorted order.
        ids = [n["id"] for n in nodes]
        assert ids == sorted(ids), "nodes are id-sorted"

        # Type filter.
        assets = _ok(
            client.get(f"/api/v1/graph/nodes?type=ASSET&context={_CTX}&as_of={_AS_OF}")
        )["data"]
        assert len(assets) == 1 and assets[0]["type"] == "ASSET", "type filter works"

        # Pagination.
        page = _ok(
            client.get(
                f"/api/v1/graph/nodes?limit=1&offset=1&context={_CTX}&as_of={_AS_OF}"
            )
        )
        assert len(page["data"]) == 1 and page["metadata"]["offset"] == 1

        # Unknown type → flat error envelope.
        bad = client.get(f"/api/v1/graph/nodes?type=BOGUS&as_of={_AS_OF}")
        assert bad.status_code == 400
        err = bad.json()
        assert err["success"] is False and err["error_code"] == "INVALID_REQUEST"


# --------------------------------------------------------------------------- #
# 3. graph_view_endpoint                                                       #
# --------------------------------------------------------------------------- #

def test_graph_view_endpoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=Path(tmp))
        _seed(layout)
        client = _client(tmp)

        body = _ok(client.get(f"/api/v1/graph/view?context={_CTX}&as_of={_AS_OF}"))
        data = body["data"]
        assert data["context"] == _CTX and data["as_of"] == _AS_OF
        assert len(data["nodes"]) == 3, "resolved view has 3 nodes"
        assert len(data["edges"]) == 2, "resolved view has 2 edges (HOSTS, IN_ZONE)"
        # Every node carries explainable confidence + provenance.
        for node in data["nodes"]:
            assert 0.0 <= node["confidence"] <= 1.0
            assert node["provenance"] in {"OBSERVED", "VERIFIED", "INFERRED"}


# --------------------------------------------------------------------------- #
# 4. analysis_risk_endpoint                                                    #
# --------------------------------------------------------------------------- #

def test_analysis_risk_endpoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=Path(tmp))
        _seed(layout)
        client = _client(tmp)

        body = _ok(client.get(f"/api/v1/analysis/risk?context={_CTX}&as_of={_AS_OF}"))
        findings = body["data"]
        assert isinstance(findings, list) and findings, "risk findings present"
        valid_categories = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for f in findings:
            assert f["category"] in valid_categories, f"valid risk band: {f}"
            assert 0 <= f["score"] <= 100, "score in range"
            assert "contributing_factors" in f, "risk is explainable"
        # At least one entity carries non-zero risk (the public-zone asset).
        assert any(f["score"] > 0 for f in findings), "exposure drives non-zero risk"


# --------------------------------------------------------------------------- #
# 5. event_replay_endpoint                                                     #
# --------------------------------------------------------------------------- #

def test_event_replay_endpoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=Path(tmp))
        _seed(layout)
        client = _client(tmp)

        body = _ok(client.get("/api/v1/events/replay"))
        events = body["data"]
        assert events, "events replayed"
        # Canonical (timestamp, id) ordering.
        keys = [(e["timestamp"], e["id"]) for e in events]
        assert keys == sorted(keys), "replay is in canonical order"

        # Count endpoint agrees.
        count_body = _ok(client.get("/api/v1/events/count"))
        assert count_body["data"]["count"] == len(events), "count matches replay"

        # as-of filtering excludes nothing here (all at t=100); sanity check shape.
        as_of_body = _ok(client.get("/api/v1/events/as-of/150"))
        assert all(e["timestamp"] <= 150 for e in as_of_body["data"])


# --------------------------------------------------------------------------- #
# 6. persistence_save_load                                                     #
# --------------------------------------------------------------------------- #

def test_persistence_save_load() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=Path(tmp))
        store = _seed(layout)
        expected_hash = PersistentGraphStore(layout).save(store)  # canonical hash
        client = _client(tmp)

        # Load reports the persisted counts and hash.
        load_body = _ok(client.post("/api/v1/persistence/load"))
        assert load_body["data"]["loaded"] is True
        assert load_body["data"]["hash"] == expected_hash, "load hash is canonical"
        assert load_body["data"]["counts"]["nodes"] == 3

        # Save re-persists the same content → identical hash (idempotent).
        save_body = _ok(client.post("/api/v1/persistence/save"))
        assert save_body["data"]["saved"] is True
        assert save_body["data"]["hash"] == expected_hash, "save→load is byte-stable"


# --------------------------------------------------------------------------- #
# 7. checkpoint_restore                                                        #
# --------------------------------------------------------------------------- #

def test_checkpoint_restore() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=Path(tmp))
        _seed(layout)
        client = _client(tmp)

        cp = _ok(client.post("/api/v1/persistence/checkpoint/cp1"))
        assert cp["data"]["checkpoint"] == "cp1"

        listed = _ok(client.get("/api/v1/persistence/checkpoints"))
        assert "cp1" in listed["data"], "checkpoint listed"

        restored = _ok(client.post("/api/v1/persistence/restore/cp1"))
        assert restored["data"]["restored"] == "cp1"
        assert restored["data"]["counts"]["nodes"] == 3, "restore reconstructs graph"

        # Restoring a missing checkpoint → 404 flat error.
        missing = client.post("/api/v1/persistence/restore/nope")
        assert missing.status_code == 404
        assert missing.json()["error_code"] == "NOT_FOUND"


# --------------------------------------------------------------------------- #
# 8. snapshot_create                                                           #
# --------------------------------------------------------------------------- #

def test_snapshot_create() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=Path(tmp))
        _seed(layout)
        client = _client(tmp)

        snap = _ok(client.post("/api/v1/persistence/snapshot/snap1"))
        assert snap["data"]["name"] == "snap1"
        assert snap["data"]["node_count"] == 3 and snap["data"]["edge_count"] == 2

        listed = _ok(client.get("/api/v1/persistence/snapshots"))
        assert any(m["name"] == "snap1" for m in listed["data"]), "snapshot listed"

        meta = _ok(client.get("/api/v1/persistence/snapshot/snap1"))
        assert meta["data"]["name"] == "snap1"
        assert meta["data"]["content_hash"] == snap["data"]["content_hash"]

        # Duplicate snapshot name → 409 conflict (immutability).
        dup = client.post("/api/v1/persistence/snapshot/snap1")
        assert dup.status_code == 409 and dup.json()["error_code"] == "CONFLICT"


# --------------------------------------------------------------------------- #
# 9. deterministic_responses                                                   #
# --------------------------------------------------------------------------- #

def test_deterministic_responses() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        layout = StorageLayout(root=Path(tmp))
        _seed(layout)
        client = _client(tmp)

        url = f"/api/v1/analysis/risk?context={_CTX}&as_of={_AS_OF}"
        first = _ok(client.get(url))
        second = _ok(client.get(url))
        # The data + confidence + metadata are fully determined by (context,
        # as_of) and on-disk state; only the envelope timestamp may differ.
        assert first["data"] == second["data"], "identical inputs → identical data"
        assert first["metadata"] == second["metadata"], "metadata is deterministic"

        # The resolved graph view is likewise stable.
        view_url = f"/api/v1/graph/view?context={_CTX}&as_of={_AS_OF}"
        assert _ok(client.get(view_url))["data"] == _ok(client.get(view_url))["data"]


# --------------------------------------------------------------------------- #
# 10. insertion_order_independence                                            #
# --------------------------------------------------------------------------- #

def test_insertion_order_independence() -> None:
    forward = _sample_observations()
    reverse = list(reversed(forward))

    def nodes_for(observations: list[Observation]) -> object:
        with tempfile.TemporaryDirectory() as tmp:
            layout = StorageLayout(root=Path(tmp))
            layout.ensure_dirs()
            store, _events = _build_store(observations)
            PersistentGraphStore(layout).save(store)
            client = _client(tmp)
            view = _ok(
                client.get(f"/api/v1/graph/view?context={_CTX}&as_of={_AS_OF}")
            )
            return view["data"]

    assert nodes_for(forward) == nodes_for(reverse), (
        "API output is independent of observation insertion order"
    )


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

_TESTS: list[tuple[str, Callable[[], None]]] = [
    ("health_endpoint", test_health_endpoint),
    ("graph_nodes_endpoint", test_graph_nodes_endpoint),
    ("graph_view_endpoint", test_graph_view_endpoint),
    ("analysis_risk_endpoint", test_analysis_risk_endpoint),
    ("event_replay_endpoint", test_event_replay_endpoint),
    ("persistence_save_load", test_persistence_save_load),
    ("checkpoint_restore", test_checkpoint_restore),
    ("snapshot_create", test_snapshot_create),
    ("deterministic_responses", test_deterministic_responses),
    ("insertion_order_independence", test_insertion_order_independence),
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
