"""Deterministic resolution engine for the Aegis CCEIP graph kernel.

This module is **pure**: every function is a deterministic function of its
arguments with no I/O, no clock access, and no randomness (doc ``06``). Given the
same assertions it always produces the same result, independent of the order in
which assertions were supplied.

It provides two concerns:

* **Conflict resolution / temporal reconstruction** — given the assertions about
  one entity, reconstruct its resolved :class:`~backend.graph.model.StateVersion`
  *as of* a timestamp, applying provenance → confidence → timestamp precedence
  and tracking contradictions (docs ``09``, ``10``, ``13``, ``63``).
* **Inference controls** — confidence decay per hop, the confidence floor, and
  the maximum inference depth (docs ``11``, ``12``).
"""

from __future__ import annotations

from collections.abc import Iterable

from backend.graph.model import (
    Assertion,
    Provenance,
    StateVersion,
)

# --------------------------------------------------------------------------- #
# Inference controls (docs 11, 12)                                             #
# --------------------------------------------------------------------------- #

#: Maximum number of inference hops permitted (doc ``12``).
MAX_INFERENCE_DEPTH = 3

#: Confidence multiplier applied per inference hop (docs ``11``, ``12``).
INFERENCE_DECAY = 0.8

#: Confidence values below this floor are discarded (docs ``11``, ``12``).
CONFIDENCE_FLOOR = 0.25


def decayed_confidence(base: float, depth: int) -> float:
    """Return ``base`` confidence after ``depth`` inference hops.

    ``confidence × decay_factor`` is applied once per hop (doc ``11``).
    """
    if depth < 0:
        raise ValueError("depth must be >= 0")
    return base * (INFERENCE_DECAY ** depth)


def inference_admissible(base: float, depth: int) -> tuple[bool, float]:
    """Decide whether an inferred fact at ``depth`` hops is admissible.

    Returns ``(admissible, decayed_confidence)``. A fact is admissible only when
    the depth is within ``1..MAX_INFERENCE_DEPTH`` and the decayed confidence is
    at or above :data:`CONFIDENCE_FLOOR` (doc ``12``).
    """
    if depth < 1 or depth > MAX_INFERENCE_DEPTH:
        return False, decayed_confidence(base, max(depth, 0))
    conf = decayed_confidence(base, depth)
    return conf >= CONFIDENCE_FLOOR, conf


# --------------------------------------------------------------------------- #
# Conflict resolution / temporal reconstruction                                #
# --------------------------------------------------------------------------- #

def _ranking_key(assertion: Assertion) -> tuple:
    """Total, order-independent ordering key for conflict resolution.

    Precedence (doc ``10``, ``13``):
    1. provenance (higher wins),
    2. confidence (higher wins),
    3. observed_at timestamp (later wins),
    4. assertion id (lexicographic) — a deterministic final tie-break that makes
       the ordering total and independent of insertion order.
    """
    return (
        -int(assertion.provenance),
        -assertion.confidence,
        -assertion.observed_at,
        assertion.id,
    )


def applicable_assertions(
    assertions: Iterable[Assertion],
    *,
    target_id: str,
    context: str,
    as_of: float,
) -> list[Assertion]:
    """Return the assertions for one entity+context that are valid at ``as_of``.

    The result is sorted by :func:`_ranking_key`, so it is fully determined by
    content and not by input order. TTL expiry is honoured via
    :meth:`Assertion.applies_at`.
    """
    selected = [
        a
        for a in assertions
        if a.target_id == target_id
        and a.context == context
        and a.applies_at(as_of)
    ]
    selected.sort(key=_ranking_key)
    return selected


def resolve_state(
    assertions: Iterable[Assertion],
    *,
    target_id: str,
    target_kind: str,
    context: str,
    as_of: float,
) -> StateVersion | None:
    """Reconstruct the resolved state of one entity as of ``as_of``.

    Returns ``None`` when no assertion applies (the entity did not exist at that
    time). Otherwise returns the winning :class:`StateVersion`, recording every
    contributing assertion and any contradictions — assertions that apply but
    disagree with the winner's value (doc ``10``).

    UNKNOWN never wins over a higher provenance because of the ranking; if the
    only applicable assertions are UNKNOWN, the winner is UNKNOWN and the
    resulting state is flagged ``is_unknown`` for exclusion from computable
    views.
    """
    applicable = applicable_assertions(
        assertions, target_id=target_id, context=context, as_of=as_of
    )
    if not applicable:
        return None

    winner = applicable[0]
    winner_value_key = winner.value_key()

    contradictions = tuple(
        sorted(
            (
                {
                    "assertion_id": a.id,
                    "provenance": a.provenance.name,
                    "confidence": a.confidence,
                    "value": a.value,
                }
                for a in applicable
                if a.id != winner.id and a.value_key() != winner_value_key
            ),
            key=lambda c: c["assertion_id"],
        )
    )

    contributing = tuple(a.id for a in applicable)  # already deterministically sorted

    return StateVersion(
        target_kind=target_kind,
        target_id=target_id,
        context=context,
        as_of=as_of,
        value=dict(winner.value),
        provenance=winner.provenance,
        confidence=winner.confidence,
        source=winner.source,
        valid_from=winner.valid_from,
        valid_to=winner.effective_valid_to,
        winner=winner.id,
        contributing=contributing,
        contradictions=contradictions,
    )
