# 47_LDAP_Integration.md

Version: 1.0

---

# Purpose

Provide enterprise directory visibility for organizations using LDAP-compatible directory services.

LDAP acts as an identity source feeding users, groups, permissions, and trust relationships into the Aegis Knowledge Graph.

---

# Supported Platforms

OpenLDAP

389 Directory Server

Apache Directory

Oracle Directory Server

Enterprise LDAP Implementations

---

# Objects Collected

Users

Groups

Organizational Units

Roles

Service Accounts

Directory Policies

---

# User Collection

Collect:

* Distinguished Name
* Username
* Email
* Last Login
* Account Status
* Group Membership

---

# Group Collection

Collect:

* Group Name
* Members
* Nested Groups
* Administrative Groups

---

# Organizational Unit Collection

Collect:

* OU Structure
* Department Mapping
* Hierarchy Relationships

---

# Identity Graph Mapping

LDAP User → IDENTITY

LDAP Group → IDENTITY

OU → ZONE

Membership → MEMBER_OF

Directory Permission → HAS_PERMISSION

---

# Risk Indicators

Dormant Accounts

Privileged Accounts

Excessive Group Membership

Service Account Exposure

Weak Directory Structure

---

# Drift Detection

New Accounts

Deleted Accounts

Privilege Changes

Group Membership Changes

---

# Goal

Provide centralized directory visibility and identity intelligence.
