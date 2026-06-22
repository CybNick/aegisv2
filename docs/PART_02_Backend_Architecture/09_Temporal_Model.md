# Temporal Model

Version: 1.0

---

## Principle

History is never destroyed.

---

## State Evolution

Old state remains preserved.

New observations create new versions.

---

## Timeline Structure

Each state contains:

* Valid From
* Valid To
* Confidence
* Source

---

## Time Travel

Supported query:

AS OF timestamp

Example:

Show environment as it existed 30 days ago.

---

## Change Tracking

Track:

* New assets
* Removed assets
* Service changes
* Identity changes
* Permission changes

---

## Drift Detection

Compares:

State A
vs
State B

Produces:

* Added
* Removed
* Modified

---

## Reconstruction

Past environments can be reconstructed exactly.

---

## Design Goal

Aegis must answer:

"What changed?"

for any time period.
