# 63_Temporal_Data_Model.md

Version: 1.0

---

# Purpose

Support infrastructure history, change tracking, and AS-OF analysis.

Time is a first-class concept throughout Aegis.

---

# Design Rule

Nothing is deleted.

Nothing is overwritten.

Everything is versioned.

---

# Version Structure

Version ID

Entity ID

Timestamp

Source

Confidence

Previous Version

Current Version

---

# Time Concepts

First Seen

Last Seen

Valid From

Valid To

Observed At

Verified At

---

# State Reconstruction

Current state is calculated.

Historical state is reconstructed.

State is never stored as mutable truth.

---

# AS-OF Queries

Examples:

Infrastructure on Jan 1

Identity state last week

Exposure state last month

Asset inventory yesterday

---

# Temporal Relationships

Relationships also contain:

Valid From

Valid To

Confidence

Source

---

# Drift Detection

Compare:

State A

State B

Generate:

Added

Removed

Modified

---

# Temporal Retention

Historical versions remain accessible.

No automatic deletion of intelligence records.

Retention policies may archive older data.

---

# Outputs

Historical Reports

Change Timelines

Trend Analysis

Drift Analysis

Time Travel Queries

---

# Goal

Allow organizations to understand not only what exists now, but what existed at any point in time.
