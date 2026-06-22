# Confidence Model

Version: 1.0

---

## Purpose

Infrastructure knowledge is inherently incomplete.

Confidence allows Aegis to represent uncertainty without pretending certainty.

---

## Confidence Scale

Range:

0.0 → 1.0

Examples:

1.0 = Certain

0.9 = Highly Likely

0.7 = Likely

0.5 = Possible

0.3 = Weak Evidence

0.0 = Unknown

---

## Confidence Sources

### Direct Observation

Highest confidence.

Examples:

* API response
* DNS response
* Service banner

Default:

0.90–1.00

---

### Verified Evidence

Strong confidence.

Examples:

* Validation checks
* Configuration confirmation

Default:

0.80–0.95

---

### Rule-Based Inference

Moderate confidence.

Examples:

* Dependency inference
* Reachability inference

Default:

0.40–0.80

---

## Confidence Decay

Inference confidence decreases per hop.

Formula:

confidence × decay_factor

Default:

0.8 per hop

---

## Confidence Floor

Values below threshold are discarded.

Default:

0.25

---

## Confidence Propagation

Path confidence equals:

Minimum confidence across path

or

Product confidence model

depending on analysis mode.

---

## User Visibility

Confidence must always be visible.

Never hide uncertainty.

---

## Design Goal

Represent uncertainty honestly while remaining useful.
