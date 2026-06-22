# GCP Integration

Version: 1.0

---

# Purpose

Collect infrastructure and identity information from Google Cloud.

---

# Supported Services

Compute Engine

Cloud Storage

Cloud SQL

GKE

IAM

Projects

VPC Networks

Load Balancers

Security Command Center

---

# Infrastructure Collection

Collect:

* Projects
* Compute Instances
* Labels
* Regions
* Zones

---

# Network Collection

Collect:

* VPCs
* Firewalls
* Routes
* Public Endpoints

---

# Identity Collection

Collect:

* Users
* Service Accounts
* IAM Bindings
* Roles

---

# Security Collection

Collect:

* SCC Findings
* Public Exposure Metadata
* Security Recommendations

---

# Graph Mapping

Project → ZONE

Instance → ASSET

Service Account → IDENTITY

IAM Binding → HAS_PERMISSION

---

# Drift Detection

Track:

* New Services
* IAM Changes
* Public Exposure

---

# Goal

Provide complete GCP visibility and risk context.
