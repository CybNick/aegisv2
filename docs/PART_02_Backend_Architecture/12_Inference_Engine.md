# Inference Engine

Version: 1.0

---

## Purpose

Generate explainable relationships from observed evidence.

---

## Core Rule

Inference never creates facts without evidence.

---

## Inference Categories

### Network Inference

Examples:

* Same subnet
* Shared gateway
* Shared routing domain

---

### Service Inference

Examples:

* Web application depends on database
* Application depends on cache

---

### Identity Inference

Examples:

* Group membership implications
* Role inheritance

---

### Infrastructure Inference

Examples:

* Shared cloud ownership
* Shared deployment pipeline

---

## Constraints

Maximum Depth:

3

---

## Confidence Decay

Each inference hop:

confidence × 0.8

---

## Inference TTL

Inferred relationships expire unless reinforced.

Default:

One collection cycle.

---

## Inference Rejection

Discard if:

* Below confidence floor
* Missing evidence
* Circular dependency detected

---

## Explainability

Every inferred relationship stores:

* Rule name
* Inputs
* Confidence
* Timestamp

---

## Design Goal

Inference should expand visibility without creating fiction.
