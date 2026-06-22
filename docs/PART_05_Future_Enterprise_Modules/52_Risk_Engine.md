# 52_Risk_Engine.md

Version: 1.0

---

# Purpose

The Risk Engine transforms infrastructure observations into explainable risk insights.

Risk is calculated using evidence, relationships, business importance, exposure, and confidence.

---

# Design Principles

Risk must be:

* Deterministic
* Explainable
* Reproducible
* Evidence-Based
* Temporal

---

# Inputs

Asset Inventory

Service Inventory

Identity Inventory

Exposure Analysis

Dependency Analysis

Change History

Confidence Scores

Business Importance

---

# Risk Formula

Risk Score =

Exposure
× Importance
× Connectivity
× Confidence
× Change Frequency

---

# Risk Categories

Critical

High

Medium

Low

Informational

---

# Scoring Range

0–100

0–20 → Low

21–40 → Moderate

41–60 → Elevated

61–80 → High

81–100 → Critical

---

# Risk Factors

Internet Exposure

Privileged Access

Business Criticality

Dependency Density

Configuration Changes

Identity Concentration

---

# Risk Outputs

Asset Risk

Service Risk

Identity Risk

Environment Risk

Business Unit Risk

---

# Explainability

Every score must include:

Why scored

Contributing factors

Evidence

Confidence

Timestamp

---

# Goal

Generate transparent, defensible risk assessments.
