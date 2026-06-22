# Architecture Decision Records

## ADR-001

Decision:

Local-first deployment

Reason:

Data sovereignty

---

## ADR-002

Decision:

Append-only storage

Reason:

Historical accuracy

---

## ADR-003

Decision:

Confidence-scored graph

Reason:

Avoid false certainty

---

## ADR-004

Decision:

Deterministic outputs

Reason:

Reproducibility

---

## ADR-005

Decision:

Temporal state model

Reason:

Infrastructure drift visibility

---

## ADR-006

Decision:

React + TypeScript + Vite for Frontend Stack

Reason:

The complexity of the UI (Dashboard, Timeline, Graph Explorer, APQL) justifies a component-based architecture over the original Vanilla JS constraint, while maintaining local-first, zero-telemetry constraints.

---

Decision

Context

Alternatives

Chosen Solution

Consequences

Date

Owner
