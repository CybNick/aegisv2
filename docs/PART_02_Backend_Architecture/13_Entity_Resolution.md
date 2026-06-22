# Entity Resolution

Version: 1.0

---

## Purpose

Merge duplicate observations into a single logical entity.

---

## Asset Resolution

Priority Order:

1. MAC Address
2. Cloud Resource ID
3. Hostname
4. IP Address

---

## Identity Resolution

Priority Order:

1. Unique Principal
2. Directory SID
3. IAM Identifier
4. Email

---

## Service Resolution

Priority Order:

1. Asset + Port
2. Product Signature
3. Service Metadata

---

## Merge Rules

Merge only when confidence exceeds threshold.

Default:

0.85

---

## Conflict Handling

Conflicting values remain preserved.

Resolver selects winning value using:

1. Provenance
2. Confidence
3. Timestamp

---

## Auditability

Every merge records:

* Inputs
* Resolution method
* Confidence
* Timestamp

---

## Design Goal

Prevent duplication while preserving evidence.
