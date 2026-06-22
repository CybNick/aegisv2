# Storage Architecture

Version: 1.0

---

# Purpose

Provide deterministic, append-only, auditable persistence for all Aegis data.

The storage layer is the system of record for:

* Events
* Graph entities
* Relationships
* Historical state
* Evidence
* Analysis results
* Reports

---

# Design Principles

Storage must be:

* Deterministic
* Auditable
* Append-only
* Recoverable
* Portable
* Local-first

---

# Storage Components

## Event Store

Stores immutable events.

Examples:

* Asset discovered
* Service detected
* Risk updated
* Relationship inferred

Purpose:

Reconstruct system history.

---

## Graph Store

Stores:

* Nodes
* Relationships
* Metadata

Acts as the operational knowledge graph.

---

## Historical Store

Stores:

* State versions
* Change history
* Temporal snapshots

Supports:

AS OF queries

Historical reconstruction

---

## Evidence Store

Stores:

* Raw observations
* Validation records
* Supporting metadata

Every graph fact references evidence.

---

## Report Store

Stores:

* Generated reports
* Scheduled reports
* Historical reports

---

# Storage Model

## Append-Only Rule

No destructive updates.

Changes create new records.

Previous records remain preserved.

---

## Versioning

All entities support:

* Version ID
* Valid From
* Valid To
* Confidence
* Provenance

---

# Local Persistence

Default storage:

~/.aegis/

Structure:

aegis/
├── graph/
├── events/
├── evidence/
├── reports/
├── exports/
├── logs/

---

# Backup Support

Supported:

* Manual backup
* Scheduled backup
* Export archive

---

# Recovery

System must support:

* Event replay
* Graph reconstruction
* Historical recovery

---

# Future Extensions

Pluggable adapters:

* SQLite
* PostgreSQL
* Neo4j
* DuckDB
* Object Storage

Core architecture must remain unchanged.

---

# Design Goal

A complete environment history must be reconstructable from storage alone.
