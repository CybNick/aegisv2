# 51_Identity_Provider_Integration.md

Version: 1.0

---

# Purpose

Provide visibility into modern identity systems and access relationships.

---

# Supported Providers

Microsoft Entra ID

Okta

Ping Identity

Google Workspace

Auth0

OneLogin

JumpCloud

Duo

---

# Identity Collection

Collect:

* Users
* Groups
* Roles
* MFA Status
* Access Policies

---

# Access Collection

Collect:

* Application Assignments
* Role Assignments
* Conditional Access Policies

---

# Authentication Metadata

Collect:

* Last Login
* Authentication Methods
* Failed Login Statistics

---

# Graph Mapping

User → IDENTITY

Group → IDENTITY

Application → SERVICE

Role → HAS_PERMISSION

Conditional Access → TRUSTS

---

# Risk Indicators

Inactive Accounts

Privileged Accounts

Missing MFA

Unused Applications

Over-Permissioned Roles

---

# Drift Detection

New Users

Deleted Users

Role Changes

Application Assignment Changes

Policy Changes

---

# Identity-Centric Analysis

Determine:

Who has access?

What systems are accessible?

Which identities are critical?

How permissions change over time?

---

# Goal

Provide unified identity visibility across cloud and enterprise platforms.
