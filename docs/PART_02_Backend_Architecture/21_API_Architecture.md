# API Architecture

Version: 1.0

---

# Purpose

Provide communication between:

* Frontend
* Backend
* Analysis engine
* Connectors
* Reporting system

---

# API Principles

APIs must be:

* Deterministic
* Stateless
* Explainable
* Versioned
* Auditable

---

# API Categories

## System APIs

Examples:

/api/system/status

/api/system/version

/api/system/health

---

## Scan APIs

Examples:

/api/scan/start

/api/scan/stop

/api/scan/history

/api/scan/results

---

## Asset APIs

Examples:

/api/assets

/api/assets/{id}

/api/assets/search

---

## Identity APIs

Examples:

/api/identities

/api/identities/{id}

---

## Service APIs

Examples:

/api/services

/api/services/{id}

---

## Graph APIs

Examples:

/api/graph

/api/graph/view

/api/graph/neighbors

/api/graph/path

---

## Analysis APIs

Examples:

/api/analysis/exposure

/api/analysis/risk

/api/analysis/dependencies

/api/analysis/criticality

---

## Timeline APIs

Examples:

/api/history

/api/history/drift

/api/history/asof

---

## Monitoring APIs

Examples:

/api/monitoring

/api/alerts

/api/events

---

## Reporting APIs

Examples:

/api/reports

/api/reports/generate

/api/reports/download

---

## Export APIs

Examples:

/api/export/json

/api/export/csv

/api/export/pdf

---

# API Response Structure

Every response contains:

{
success,
timestamp,
data,
confidence,
metadata
}

---

# Error Structure

{
success: false,
error_code,
message,
details
}

---

# Authentication Model

Version 1:

Local-only

Single-user

Future:

* Multi-user
* RBAC
* SSO

---

# WebSocket Support

Used for:

* Live scans
* Progress updates
* Monitoring events
* Dashboard refreshes

---

# Versioning

Pattern:

/api/v1/

Future versions:

/api/v2/

/api/v3/

---

# Integration Boundaries

Future connectors:

* AWS
* Azure
* GCP
* Active Directory
* LDAP
* Kubernetes
* SIEM Platforms

must interact through APIs rather than direct database access.

---

# Design Goal

All platform capabilities must be accessible through stable APIs.
