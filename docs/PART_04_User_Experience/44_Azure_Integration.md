# Azure Integration

Version: 1.0

---

# Purpose

Collect Azure infrastructure, networking, and identity data.

---

# Supported Services

Virtual Machines

Virtual Networks

Azure AD

AKS

Storage Accounts

SQL Databases

App Services

Key Vault

Subscriptions

Defender for Cloud

---

# Infrastructure Collection

Collect:

* VM Metadata
* Regions
* Resource Groups
* Tags
* Availability Sets

---

# Network Collection

Collect:

* VNets
* Subnets
* NSGs
* Public IPs
* Route Tables

---

# Identity Collection

Collect:

* Users
* Groups
* Service Principals
* Managed Identities
* Role Assignments

---

# Security Collection

Collect:

* Defender Findings
* Exposure Recommendations
* Identity Risk Metadata

---

# Graph Mapping

Subscription → ZONE

VM → ASSET

Identity → IDENTITY

Role Assignment → HAS_PERMISSION

---

# Drift Detection

Track:

* New Resources
* Role Changes
* Public Exposure Changes

---

# Goal

Provide full Azure infrastructure awareness.
