"""Deterministic self-tests for the Aegis CCEIP graph kernel (Milestone 2).

Run with::

    python -m backend.graph.selftest

On success the final line is exactly ``ALL PASS`` and the process exits 0. On any
failure the offending check is printed and the process exits non-zero.

The tests use **logical integer timestamps** and explicit confidences so that
every result is fully determined by content — there is no wall-clock or random
input anywhere in the kernel or these tests.

Covered scenarios:

1. Contradiction resolution (provenance / confidence / timestamp precedence)
2. Inference decay (+ confidence floor, max depth, TTL expiry)
3. Context separation
4. Temporal reconstruction (AS OF)
5. UNKNOWN exclusion
6. Determinism across shuffled insertion order
7. Context enforcement
8. Canonical serialization
"""

from __future__ import annotations

import json
import math
import sys
from collections.abc import Callable

from backend.graph.model import (
    EdgeType,
    NodeType,
    Provenance,
)
from backend.graph.resolver import (
    CONFIDENCE_FLOOR,
    MAX_INFERENCE_DEPTH,
    decayed_confidence,
    inference_admissible,
)
from backend.graph.store import GraphStore

_EV = ("evidence:selftest",)


# --------------------------------------------------------------------------- #
# 1. Contradiction resolution                                                  #
# --------------------------------------------------------------------------- #

def test_contradiction_resolution() -> None:
    # Provenance precedence: OBSERVED beats INFERRED even with lower confidence.
    store = GraphStore()
    node = store.ensure_node(NodeType.SERVICE, {"name": "ssh"})
    store.assert_node(
        node, value={"state": "open"}, provenance=Provenance.OBSERVED,
        confidence=0.90, source="scan", valid_from=0, observed_at=5, evidence=_EV,
    )
    store.assert_node(
        node, value={"state": "closed"}, provenance=Provenance.INFERRED,
        confidence=0.95, source="rule", valid_from=0, observed_at=10,
        evidence=_EV, inferred_depth=1,
    )
    state = store.state_of(node.id, context="default", as_of=20)
    assert state is not None
    assert state.provenance is Provenance.OBSERVED, "OBSERVED must win on provenance"
    assert state.value == {"state": "open"}
    assert len(state.contradictions) == 1, "the disagreeing inferred fact is tracked"
    assert state.contradictions[0]["provenance"] == "INFERRED"

    # Confidence precedence: same provenance -> higher confidence wins.
    store2 = GraphStore()
    n2 = store2.ensure_node(NodeType.ASSET, {"host": "h1"})
    store2.assert_node(
        n2, value={"os": "linux"}, provenance=Provenance.OBSERVED,
        confidence=0.70, source="a", valid_from=0, observed_at=1, evidence=_EV,
    )
    store2.assert_node(
        n2, value={"os": "windows"}, provenance=Provenance.OBSERVED,
        confidence=0.95, source="b", valid_from=0, observed_at=1, evidence=_EV,
    )
    s2 = store2.state_of(n2.id, context="default", as_of=10)
    assert s2 is not None and s2.value == {"os": "windows"}, "higher confidence wins"

    # Timestamp precedence: same provenance + confidence -> later observed_at wins.
    store3 = GraphStore()
    n3 = store3.ensure_node(NodeType.ASSET, {"host": "h2"})
    store3.assert_node(
        n3, value={"ip": "10.0.0.1"}, provenance=Provenance.OBSERVED,
        confidence=0.90, source="a", valid_from=0, observed_at=5, evidence=_EV,
    )
    store3.assert_node(
        n3, value={"ip": "10.0.0.2"}, provenance=Provenance.OBSERVED,
        confidence=0.90, source="b", valid_from=0, observed_at=9, evidence=_EV,
    )
    s3 = store3.state_of(n3.id, context="default", as_of=10)
    assert s3 is not None and s3.value == {"ip": "10.0.0.2"}, "later timestamp wins"


# --------------------------------------------------------------------------- #
# 2. Inference decay (+ floor, max depth, TTL)                                 #
# --------------------------------------------------------------------------- #

def test_inference_decay() -> None:
    assert math.isclose(decayed_confidence(1.0, 1), 0.8)
    assert math.isclose(decayed_confidence(1.0, 2), 0.64)
    assert math.isclose(decayed_confidence(1.0, 3), 0.512)

    ok3, _ = inference_admissible(1.0, MAX_INFERENCE_DEPTH)
    assert ok3, "depth 3 within limit is admissible"

    ok4, _ = inference_admissible(1.0, MAX_INFERENCE_DEPTH + 1)
    assert not ok4, "depth beyond 3 is rejected"

    ok_floor, conf = inference_admissible(0.30, 1)
    assert not ok_floor and conf < CONFIDENCE_FLOOR, "below floor is rejected"

    # TTL expiry: an inferred fact expires at valid_from + ttl unless reinforced.
    store = GraphStore()
    a = store.ensure_node(NodeType.ASSET, {"host": "src"})
    b = store.ensure_node(NodeType.ASSET, {"host": "dst"})
    edge = store.ensure_edge(EdgeType.CONNECTS_TO, a, b, context="default")
    store.assert_edge(
        edge, value={"exists": True}, provenance=Provenance.INFERRED,
        confidence=0.8, source="rule", valid_from=0, evidence=_EV,
        inferred_depth=1, ttl=10,
    )
    assert store.state_of(edge.id, context="default", as_of=5, target_kind="edge")
    assert store.state_of(edge.id, context="default", as_of=15, target_kind="edge") is None, \
        "inferred fact must expire after its TTL"


# --------------------------------------------------------------------------- #
# 3. Context separation                                                        #
# --------------------------------------------------------------------------- #

def test_context_separation() -> None:
    store = GraphStore()
    a = store.ensure_node(NodeType.ASSET, {"host": "a"})
    b = store.ensure_node(NodeType.ASSET, {"host": "b"})
    prod = store.ensure_edge(EdgeType.CONNECTS_TO, a, b, context="prod")
    dev = store.ensure_edge(EdgeType.CONNECTS_TO, a, b, context="dev")
    assert prod.id != dev.id, "same edge in different contexts has distinct identity"

    store.assert_edge(
        prod, value={"exists": True}, provenance=Provenance.OBSERVED,
        confidence=0.9, source="scan", valid_from=0, evidence=_EV,
    )
    prod_view = store.computable_view(context="prod", as_of=10)
    dev_view = store.computable_view(context="dev", as_of=10)
    assert prod.id in prod_view, "prod assertion visible in prod view"
    assert dev.id not in prod_view, "dev edge not in prod view"
    assert dev_view == {}, "dev context has no facts"


# --------------------------------------------------------------------------- #
# 4. Temporal reconstruction                                                   #
# --------------------------------------------------------------------------- #

def test_temporal_reconstruction() -> None:
    store = GraphStore()
    node = store.ensure_node(NodeType.ASSET, {"host": "timebox"})
    store.assert_node(
        node, value={"v": "A"}, provenance=Provenance.OBSERVED,
        confidence=0.9, source="s", valid_from=10, valid_to=20,
        observed_at=10, evidence=_EV,
    )
    store.assert_node(
        node, value={"v": "B"}, provenance=Provenance.OBSERVED,
        confidence=0.9, source="s", valid_from=20, observed_at=20, evidence=_EV,
    )
    assert store.state_of(node.id, context="default", as_of=5) is None, "absent before"
    assert store.state_of(node.id, context="default", as_of=15).value == {"v": "A"}
    assert store.state_of(node.id, context="default", as_of=20).value == {"v": "B"}, \
        "valid_to is exclusive; new version starts at 20"
    assert store.state_of(node.id, context="default", as_of=25).value == {"v": "B"}


# --------------------------------------------------------------------------- #
# 5. UNKNOWN exclusion                                                         #
# --------------------------------------------------------------------------- #

def test_unknown_exclusion() -> None:
    store = GraphStore()
    unknown = store.ensure_node(NodeType.ASSET, {"host": "ghost"})
    store.assert_node(
        unknown, value={"state": "?"}, provenance=Provenance.UNKNOWN,
        confidence=0.0, source="?", valid_from=0,
    )
    view = store.computable_view(context="default", as_of=10)
    assert unknown.id not in view, "UNKNOWN entity excluded from computable view"
    state = store.state_of(unknown.id, context="default", as_of=10)
    assert state is not None and state.is_unknown, "but still reconstructable as UNKNOWN"

    # UNKNOWN never wins a conflict against a real observation.
    known = store.ensure_node(NodeType.ASSET, {"host": "real"})
    store.assert_node(
        known, value={"state": "?"}, provenance=Provenance.UNKNOWN,
        confidence=1.0, source="?", valid_from=0,
    )
    store.assert_node(
        known, value={"state": "up"}, provenance=Provenance.OBSERVED,
        confidence=0.5, source="scan", valid_from=0, observed_at=1, evidence=_EV,
    )
    view2 = store.computable_view(context="default", as_of=10)
    assert known.id in view2 and view2[known.id].value == {"state": "up"}, \
        "OBSERVED beats even maximally-confident UNKNOWN"


# --------------------------------------------------------------------------- #
# 6. Determinism across shuffled insertion order                               #
# --------------------------------------------------------------------------- #

_SPECS = [
    # (node_key, value, provenance, confidence, observed_at, valid_from, context)
    ({"host": "h1"}, {"os": "linux"}, Provenance.OBSERVED, 0.9, 3, 0, "prod"),
    ({"host": "h1"}, {"os": "bsd"}, Provenance.INFERRED, 0.95, 8, 0, "prod"),
    ({"host": "h2"}, {"role": "db"}, Provenance.VERIFIED, 0.85, 2, 0, "prod"),
    ({"host": "h2"}, {"role": "cache"}, Provenance.VERIFIED, 0.85, 7, 0, "dev"),
    ({"host": "h3"}, {"zone": "dmz"}, Provenance.OBSERVED, 0.7, 1, 0, "prod"),
    ({"host": "h3"}, {"zone": "internal"}, Provenance.OBSERVED, 0.7, 6, 0, "prod"),
]


def _build_from(order: list[int]) -> GraphStore:
    store = GraphStore()
    for i in order:
        key, value, prov, conf, obs, vf, ctx = _SPECS[i]
        node = store.ensure_node(NodeType.ASSET, key)
        store.assert_node(
            node, value=value, provenance=prov, confidence=conf, source="s",
            valid_from=vf, observed_at=obs, context=ctx,
            evidence=() if prov is Provenance.UNKNOWN else _EV,
        )
    return store


def test_determinism_shuffled_order() -> None:
    forward = list(range(len(_SPECS)))
    reverse = list(reversed(forward))
    interleaved = forward[::2] + forward[1::2]

    s_fwd = _build_from(forward).serialize()
    s_rev = _build_from(reverse).serialize()
    s_int = _build_from(interleaved).serialize()
    assert s_fwd == s_rev == s_int, "serialization is independent of insertion order"

    def view_repr(store: GraphStore) -> str:
        view = store.computable_view(context="prod", as_of=100)
        return json.dumps(
            {k: v.to_dict() for k, v in sorted(view.items())},
            sort_keys=True, separators=(",", ":"),
        )

    assert view_repr(_build_from(forward)) == view_repr(_build_from(reverse)), \
        "computable view is independent of insertion order"


# --------------------------------------------------------------------------- #
# 7. Context enforcement                                                       #
# --------------------------------------------------------------------------- #

def test_context_enforcement() -> None:
    store = GraphStore()
    node = store.ensure_node(NodeType.ASSET, {"host": "scoped"})
    store.assert_node(
        node, value={"env": "prod"}, provenance=Provenance.OBSERVED,
        confidence=0.9, source="scan", valid_from=0, observed_at=1,
        context="prod", evidence=_EV,
    )
    assert store.state_of(node.id, context="prod", as_of=10) is not None
    assert store.state_of(node.id, context="dev", as_of=10) is None, \
        "a fact asserted in prod must not leak into dev"
    assert store.computable_view(context="dev", as_of=10) == {}, \
        "querying another context yields no facts"


# --------------------------------------------------------------------------- #
# 8. Canonical serialization                                                   #
# --------------------------------------------------------------------------- #

def test_canonical_serialization() -> None:
    store = _build_from(list(range(len(_SPECS))))

    s1 = store.serialize()
    s2 = store.serialize()
    assert s1 == s2, "serialization is stable across calls"

    # Round-trip: load -> serialize reproduces the exact canonical form.
    assert GraphStore.load(s1).serialize() == s1, "round-trip is lossless and canonical"

    parsed = json.loads(s1)
    # Top-level keys are sorted alphabetically by canonical serialization.
    assert list(parsed.keys()) == sorted(parsed.keys()), "object keys are sorted"
    # Assertion ids appear in sorted order.
    ids = [a["id"] for a in parsed["assertions"]]
    assert ids == sorted(ids), "assertions serialized in deterministic id order"


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

_TESTS: list[tuple[str, Callable[[], None]]] = [
    ("contradiction_resolution", test_contradiction_resolution),
    ("inference_decay", test_inference_decay),
    ("context_separation", test_context_separation),
    ("temporal_reconstruction", test_temporal_reconstruction),
    ("unknown_exclusion", test_unknown_exclusion),
    ("determinism_shuffled_order", test_determinism_shuffled_order),
    ("context_enforcement", test_context_enforcement),
    ("canonical_serialization", test_canonical_serialization),
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
