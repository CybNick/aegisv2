# 49_Container_Registry_Integration.md

Version: 1.0

---

# Purpose

Provide visibility into container image inventory and software supply chain metadata.

---

# Supported Registries

Docker Hub

Amazon ECR

Azure Container Registry

Google Artifact Registry

Harbor

GitHub Container Registry

GitLab Registry

JFrog Artifactory

---

# Image Discovery

Collect:

* Repository Names
* Tags
* Digests
* Creation Dates
* Owners

---

# Metadata Collection

Collect:

* Base Images
* Image Layers
* Maintainers
* Labels

---

# Dependency Visibility

Track:

* Image Relationships
* Parent Images
* Runtime Usage

---

# Vulnerability Metadata

Import:

* Registry Findings
* Security Metadata
* Compliance Metadata

No active scanning required.

---

# Graph Mapping

Image → SERVICE

Registry → ZONE

Dependency → DEPENDS_ON

Maintainer → IDENTITY

---

# Risk Indicators

Outdated Images

Unmaintained Images

Public Registries

Excessive Image Proliferation

Unknown Ownership

---

# Drift Detection

New Images

Deleted Images

Tag Changes

Base Image Changes

---

# Goal

Provide software supply chain visibility and image governance.
