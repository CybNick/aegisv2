# Graph Kernel

Version: 1.0

---

## Purpose

The graph is the central intelligence model of Aegis.

Everything is represented as nodes and relationships.

---

## Node Types

### ASSET

Examples:

* Server
* Laptop
* Router
* Switch
* VM

### SERVICE

Examples:

* HTTP
* SSH
* PostgreSQL

### IDENTITY

Examples:

* User
* Service Account
* Role

### CREDENTIAL

Examples:

* Password
* Key
* Certificate

### DATASTORE

Examples:

* Database
* File Share
* Object Storage

### ZONE

Examples:

* Internet
* DMZ
* Internal Network
* VPC

---

## Relationship Types

HOSTS

IN_ZONE

RESOLVES_TO

CONNECTS_TO

DEPENDS_ON

AUTHENTICATES_TO

HAS_PERMISSION

ASSUMES_ROLE

MEMBER_OF

TRUSTS

---

## Relationship Attributes

* Confidence
* Source
* Evidence
* Timestamp
* Context

---

## Graph Requirements

* Deterministic
* Temporal
* Confidence-aware
* Explainable
* Evidence-backed

---

## Knowledge Rule

Nothing exists in the graph without evidence.
