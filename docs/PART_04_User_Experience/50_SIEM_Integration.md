# 50_SIEM_Integration.md

Version: 1.0

---

# Purpose

Enrich the Aegis Knowledge Graph using operational security telemetry.

---

# Supported Platforms

Splunk

Microsoft Sentinel

QRadar

Elastic Security

LogRhythm

Sumo Logic

Chronicle

Graylog

---

# Data Sources

Authentication Events

Network Events

Endpoint Events

Cloud Events

Security Alerts

Threat Detections

Audit Logs

---

# Collection Model

Read-only ingestion.

No modification of SIEM data.

---

# Event Normalization

Convert events into:

Observed Relationships

Observed Activity

Identity Activity

Asset Activity

Exposure Evidence

---

# Graph Mapping

Authentication → AUTHENTICATES_TO

Connection → CONNECTS_TO

Alert → Evidence

Identity Event → IDENTITY

Asset Event → ASSET

---

# Confidence Assignment

Observed telemetry receives:

Confidence ≥ 0.95

---

# Risk Enrichment

Increase confidence when:

Multiple data sources confirm activity.

Reduce confidence when:

Single-source unverified observations exist.

---

# Drift Detection

Behavior Changes

New Connections

New Identities

New Service Relationships

---

# Goal

Transform telemetry into infrastructure intelligence.
