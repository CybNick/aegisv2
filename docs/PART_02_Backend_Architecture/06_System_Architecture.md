# System Architecture

Version: 1.0

---

## Overview

Aegis CCEIP is a local-first cyber exposure and infrastructure intelligence platform.

The platform consists of five major layers:

1. Data Ingestion Layer
2. Event Processing Layer
3. Knowledge Graph Layer
4. Analysis Layer
5. Presentation Layer

---

## Layer 1 — Data Ingestion

Responsible for collecting information from authorized sources.

Sources include:

* Network inventory scans
* DNS
* Firewall logs
* Cloud APIs
* IAM systems
* Active Directory
* Kubernetes
* Container platforms
* CI/CD systems

Output:

Normalized events.

---

## Layer 2 — Event Processing

All observations become immutable events.

Examples:

* AssetDiscovered
* ServiceDetected
* RelationshipObserved
* RiskUpdated

Output:

Event stream.

---

## Layer 3 — Knowledge Graph

Stores infrastructure knowledge.

Contains:

* Assets
* Services
* Identities
* Credentials
* Datastores
* Zones

Maintains:

* Relationships
* Temporal history
* Confidence
* Evidence

---

## Layer 4 — Analysis

Responsible for:

* Exposure analysis
* Dependency analysis
* Impact analysis
* Drift analysis
* Risk scoring

---

## Layer 5 — Presentation

Provides:

* Dashboard
* Reports
* Query engine
* Visualization
* Timeline

---

## Architectural Constraints

* Deterministic
* Append-only
* Explainable
* Local-first
* Offline-capable
* Safe operation

---

## Design Goal

Same input must always generate identical graph state and analysis results.
