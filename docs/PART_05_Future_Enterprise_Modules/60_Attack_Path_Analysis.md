# 60_Attack_Path_Analysis.md

Version: 1.0

---

# Purpose

Analyze potential relationship chains between exposed entities and critical assets.

The objective is exposure reasoning, not attack execution.

---

# Design Principles

Defensive Only

Evidence-Based

Explainable

Deterministic

Non-Intrusive

---

# Inputs

Exposure Analysis

Dependency Analysis

Identity Analysis

Critical Asset Detection

Confidence Model

Verification Engine

---

# Relationship Types

EXPOSES

REACHES

DEPENDS_ON

HAS_PERMISSION

ASSUMES_ROLE

AUTHENTICATES_TO

TRUSTS

---

# Analysis Process

1. Identify Entry Points

2. Discover Reachable Relationships

3. Evaluate Confidence

4. Evaluate Critical Asset Reachability

5. Rank Results

---

# Entry Points

Internet Exposure

Public Services

Public Applications

Public Identities

---

# Path Outputs

Source

Destination

Relationship Chain

Confidence

Verification State

Risk Score

---

# Path States

Verified

Partially Verified

Theoretical

Unknown

---

# Path Ranking Factors

Business Importance

Exposure

Connectivity

Confidence

Verification

---

# Constraints

No exploitation

No credential use

No attack simulation

No autonomous actions

---

# Goal

Understand exposure pathways through infrastructure relationships.
