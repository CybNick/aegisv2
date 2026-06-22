# Provenance Model

Version: 1.0

---

## Purpose

Every fact must have a source.

---

## Provenance Levels

### OBSERVED

Collected directly.

Examples:

* Port response
* DNS record
* API response

Priority = 3

---

### VERIFIED

Safely confirmed.

Examples:

* Service confirmation
* Configuration validation

Priority = 2

---

### INFERRED

Derived through rules.

Examples:

* Dependency inference
* Reachability inference

Priority = 1

---

### UNKNOWN

Insufficient evidence.

Priority = 0

---

## Resolution Order

OBSERVED

>

VERIFIED

>

INFERRED

>

UNKNOWN

---

## Provenance Fields

Each fact stores:

* Source
* Timestamp
* Confidence
* Evidence
* Collection Method

---

## Conflict Resolution

Higher provenance always wins.

Example:

Observed firewall rule
beats

Inferred reachability

---

## Explainability

Every graph relationship must display:

* Why it exists
* Where it came from
* When it was observed

---

## Design Goal

Users should never need to trust the system blindly.

Every fact must be traceable to evidence.
