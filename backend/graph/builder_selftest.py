"""Deterministic self-tests for the Scan→Graph builder (Milestone 3).

Run with::

    python -m backend.graph.builder_selftest

On success the final line is exactly ``ALL PASS`` and the process exits 0.

The builder takes normalized observations and emits deterministic assertions
compatible with the Milestone 2 kernel. These tests use logical integer
timestamps and explicit confidences, so every result is fully determined by
content — no wall-clock or random input.

Covered scenarios:

1. Asset → node assertions
2. Service → service node + relationships
3. Identity → identity assertions
4. Datastore → datastore assertions
5. Zone → zone assertions
6. Context assignment
7. Deterministic output (shuffled order)
8. Canonical assertion generation (Milestone 2 compatibility)
9. Deduplication hook execution
10. Entity-resolution hook execution
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from backend.graph.builder import BuildResult, EntityResolver, GraphBuilder
from backend.graph.model import (
    EdgeType,
    Node,
    NodeType,
    Provenance,
    canonical_dumps,
)
from backend.graph.schemas import (
    AssetObservation,
    AssetRef,
    DatastoreObservation,
    EventType,
    IdentityObservation,
    ServiceObservation,
    ZoneObservation,
)
from backend.graph.store import GraphStore

_EV = ("evidence:selftest",)


def _node_assertions(result: BuildResult, kind: str) -> list:
    return [a for a in result.assertions if a.target_kind == kind]


# --------------------------------------------------------------------------- #
# 1. Asset → node assertions                                                   #
# --------------------------------------------------------------------------- #

def test_asset_to_node() -> None:
    obs = AssetObservation(
        ref=AssetRef(hostname="web-01"), source="scan", evidence=_EV,
        observed_at=100, attributes={"os": "linux"},
    )
    result = GraphBuilder().build([obs])
    expected = Node.create(NodeType.ASSET, {"hostname": "web-01"})

    assert len(result.nodes) == 1 and result.nodes[0].id == expected.id
    node_asserts = _node_assertions(result, "node")
    assert len(node_asserts) == 1
    a = node_asserts[0]
    assert a.target_id == expected.id
    assert a.provenance is Provenance.OBSERVED
    assert a.value == {"exists": True, "os": "linux"}
    assert [e.event_type for e in result.events] == [EventType.ASSET_DISCOVERED]


# --------------------------------------------------------------------------- #
# 2. Service → service node + relationships                                    #
# --------------------------------------------------------------------------- #

def test_service_to_node_and_edge() -> None:
    obs = ServiceObservation(
        host=AssetRef(hostname="web-01"), port=443, product_signature="nginx",
        source="scan", evidence=_EV, observed_at=100,
    )
    result = GraphBuilder().build([obs])

    host = Node.create(NodeType.ASSET, {"hostname": "web-01"})
    svc = Node.create(NodeType.SERVICE, {"asset": host.id, "port": 443})

    svc_nodes = [n for n in result.nodes if n.node_type is NodeType.SERVICE]
    assert len(svc_nodes) == 1 and svc_nodes[0].id == svc.id

    assert len(result.edges) == 1
    edge = result.edges[0]
    assert edge.edge_type is EdgeType.HOSTS
    assert edge.src == host.id and edge.dst == svc.id, "asset HOSTS service"

    edge_asserts = _node_assertions(result, "edge")
    assert len(edge_asserts) == 1 and edge_asserts[0].target_id == edge.id
    types = sorted(e.event_type.value for e in result.events)
    assert types == ["RELATIONSHIP_OBSERVED", "SERVICE_DETECTED"]


# --------------------------------------------------------------------------- #
# 3. Identity → identity assertions                                            #
# --------------------------------------------------------------------------- #

def test_identity_to_assertions() -> None:
    obs = IdentityObservation(
        principal="alice", identity_type="user", member_of=("admins",),
        source="ad", evidence=_EV, observed_at=100,
    )
    result = GraphBuilder().build([obs])

    alice = Node.create(NodeType.IDENTITY, {"principal": "alice"})
    admins = Node.create(NodeType.IDENTITY, {"principal": "admins"})

    ids = {n.id for n in result.nodes}
    assert alice.id in ids and admins.id in ids

    node_asserts = _node_assertions(result, "node")
    assert len(node_asserts) == 1 and node_asserts[0].target_id == alice.id
    assert node_asserts[0].value == {"exists": True, "identity_type": "user"}

    edge = result.edges[0]
    assert edge.edge_type is EdgeType.MEMBER_OF
    assert edge.src == alice.id and edge.dst == admins.id


# --------------------------------------------------------------------------- #
# 4. Datastore → datastore assertions                                          #
# --------------------------------------------------------------------------- #

def test_datastore_to_assertions() -> None:
    obs = DatastoreObservation(
        cloud_id="arn:rds:db-1", name="orders", source="aws", evidence=_EV,
        observed_at=100,
    )
    result = GraphBuilder().build([obs])
    expected = Node.create(NodeType.DATASTORE, {"cloud_id": "arn:rds:db-1"})

    assert len(result.nodes) == 1 and result.nodes[0].id == expected.id
    a = _node_assertions(result, "node")[0]
    assert a.target_id == expected.id
    assert a.value == {"exists": True, "name": "orders"}
    assert [e.event_type for e in result.events] == [EventType.DATASTORE_IDENTIFIED]


# --------------------------------------------------------------------------- #
# 5. Zone → zone assertions                                                    #
# --------------------------------------------------------------------------- #

def test_zone_to_assertions() -> None:
    obs = ZoneObservation(name="DMZ", source="scan", evidence=_EV, observed_at=100)
    result = GraphBuilder().build([obs])
    expected = Node.create(NodeType.ZONE, {"name": "DMZ"})

    assert len(result.nodes) == 1 and result.nodes[0].id == expected.id
    a = _node_assertions(result, "node")[0]
    assert a.value == {"exists": True, "name": "DMZ"}
    assert [e.event_type for e in result.events] == [EventType.ZONE_DISCOVERED]


# --------------------------------------------------------------------------- #
# 6. Context assignment                                                        #
# --------------------------------------------------------------------------- #

def test_context_assignment() -> None:
    obs = AssetObservation(
        ref=AssetRef(hostname="web-01"), zone="DMZ", context="prod",
        source="scan", evidence=_EV, observed_at=100,
    )
    result = GraphBuilder().build([obs])
    assert result.assertions, "expected assertions"
    assert all(a.context == "prod" for a in result.assertions), \
        "every assertion carries the observation context"
    assert all(e.context == "prod" for e in result.edges), \
        "edges are created in the observation context"


# --------------------------------------------------------------------------- #
# 7. Deterministic output (shuffled order)                                     #
# --------------------------------------------------------------------------- #

def _sample_observations() -> list:
    return [
        AssetObservation(ref=AssetRef(hostname="web-01"), zone="DMZ",
                         source="scan", evidence=_EV, observed_at=100,
                         attributes={"os": "linux"}),
        ServiceObservation(host=AssetRef(hostname="web-01"), port=443,
                           source="scan", evidence=_EV, observed_at=100),
        IdentityObservation(principal="alice", member_of=("admins",),
                            source="ad", evidence=_EV, observed_at=100),
        DatastoreObservation(cloud_id="arn:rds:db-1", source="aws",
                             evidence=_EV, observed_at=100),
        ZoneObservation(name="DMZ", source="scan", evidence=_EV, observed_at=100),
    ]


def _result_repr(result: BuildResult) -> str:
    return canonical_dumps({
        "assertions": result.assertion_dicts(),
        "nodes": [n.to_dict() for n in result.nodes],
        "edges": [e.to_dict() for e in result.edges],
        "events": [e.to_dict() for e in result.events],
    })


def test_deterministic_output() -> None:
    obs = _sample_observations()
    forward = GraphBuilder().build(obs)
    reverse = GraphBuilder().build(list(reversed(obs)))
    interleaved = GraphBuilder().build(obs[::2] + obs[1::2])

    assert _result_repr(forward) == _result_repr(reverse) == _result_repr(interleaved), \
        "build output is independent of observation order"


# --------------------------------------------------------------------------- #
# 8. Canonical assertion generation (Milestone 2 compatibility)                #
# --------------------------------------------------------------------------- #

def test_canonical_assertions_m2_compat() -> None:
    result = GraphBuilder().build(_sample_observations())

    # Assertions round-trip through the kernel serialization unchanged.
    from backend.graph.model import Assertion
    for a in result.assertions:
        assert Assertion.from_dict(a.to_dict()) == a

    # They append cleanly to a Milestone 2 store and reconstruct a view.
    store = GraphStore()
    for a in result.assertions:
        store.append(a)
    view = store.computable_view(context="default", as_of=1000)
    # The web-01 asset (asserted in the default context) is reconstructable.
    web = Node.create(NodeType.ASSET, {"hostname": "web-01"})
    assert web.id in view and view[web.id].value["exists"] is True

    # Re-appending the same assertions is idempotent (deterministic ids).
    before = store.serialize()
    for a in result.assertions:
        store.append(a)
    assert store.serialize() == before, "assertions are idempotent in the store"


# --------------------------------------------------------------------------- #
# 9. Deduplication hook execution                                              #
# --------------------------------------------------------------------------- #

def test_dedup_hook_execution() -> None:
    calls: list[str] = []

    def counting_dedup(entity_id: str) -> str:
        calls.append(entity_id)
        return entity_id

    obs = AssetObservation(ref=AssetRef(hostname="web-01"), source="scan",
                           evidence=_EV, observed_at=100)
    builder = GraphBuilder(dedup_key=counting_dedup)
    # Two identical observations must collapse to a single node + assertion.
    result = builder.build([obs, obs])

    assert calls, "deduplication hook was invoked"
    assert len(result.nodes) == 1, "identical assets deduplicated to one node"
    assert len(_node_assertions(result, "node")) == 1, "assertions deduplicated"


# --------------------------------------------------------------------------- #
# 10. Entity-resolution hook execution                                         #
# --------------------------------------------------------------------------- #

def test_entity_resolution_hook_execution() -> None:
    class CountingResolver(EntityResolver):
        def __init__(self) -> None:
            self.asset_calls = 0

        def resolve_asset(self, ref: AssetRef) -> dict[str, str]:
            self.asset_calls += 1
            return super().resolve_asset(ref)

    resolver = CountingResolver()
    # MAC present alongside hostname -> resolver must pick MAC (highest priority).
    obs = AssetObservation(
        ref=AssetRef(mac="AA:BB:CC", hostname="web-01"),
        source="scan", evidence=_EV, observed_at=100,
    )
    result = GraphBuilder(resolver=resolver).build([obs])

    assert resolver.asset_calls >= 1, "entity-resolution hook was invoked"
    by_mac = Node.create(NodeType.ASSET, {"mac": "AA:BB:CC"})
    assert result.nodes[0].id == by_mac.id, "MAC wins over hostname (doc 13 priority)"


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

_TESTS: list[tuple[str, Callable[[], None]]] = [
    ("asset_to_node", test_asset_to_node),
    ("service_to_node_and_edge", test_service_to_node_and_edge),
    ("identity_to_assertions", test_identity_to_assertions),
    ("datastore_to_assertions", test_datastore_to_assertions),
    ("zone_to_assertions", test_zone_to_assertions),
    ("context_assignment", test_context_assignment),
    ("deterministic_output", test_deterministic_output),
    ("canonical_assertions_m2_compat", test_canonical_assertions_m2_compat),
    ("dedup_hook_execution", test_dedup_hook_execution),
    ("entity_resolution_hook_execution", test_entity_resolution_hook_execution),
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
