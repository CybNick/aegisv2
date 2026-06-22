# Query Engine

Version: 1.0

---

## Purpose

Allow users to explore infrastructure knowledge efficiently.

---

## Query Types

### Structured Queries

Deterministic syntax.

Examples:

Find assets in DMZ

Find internet-facing services

Find critical databases

---

### Natural Language Queries

Examples:

"What changed this week?"

"Which systems are externally reachable?"

"Show critical assets."

---

## Query Pipeline

1. Parse request

2. Resolve entities

3. Apply filters

4. Execute graph traversal

5. Rank results

6. Return explanation

---

## Supported Operations

### Search

Locate entities.

### Filter

Reduce results.

### Aggregate

Summarize information.

### Compare

Evaluate differences.

### Historical

Execute AS OF queries.

### Relationship

Traverse graph dependencies.

---

## Result Structure

Each result includes:

* Data
* Confidence
* Evidence
* Timestamp
* Explanation

---

## Query Safety

Queries must never modify graph state.

All queries are read-only.

---

## Design Goal

Allow users to understand infrastructure through exploration.
