# Active Directory Integration

Version: 1.0

---

# Purpose

Provide identity-centric visibility across enterprise environments.

---

# Objects Collected

Users

Groups

Computers

Service Accounts

Organizational Units

Trusts

Group Policies

---

# User Collection

Collect:

* Username
* SID
* Last Login
* Password Metadata
* Group Membership

---

# Group Collection

Collect:

* Group Name
* Members
* Nested Groups
* Privilege Levels

---

# Computer Collection

Collect:

* Hostname
* OS
* Domain Membership
* Last Seen

---

# Trust Collection

Collect:

* Forest Trusts
* Domain Trusts
* External Trusts

---

# Privilege Analysis

Identify:

* Domain Admins
* Enterprise Admins
* Privileged Groups
* Service Accounts

---

# Graph Mapping

User → IDENTITY

Group → IDENTITY

Computer → ASSET

Membership → MEMBER_OF

Trust → TRUSTS

Permission → HAS_PERMISSION

---

# Drift Detection

Monitor:

* New Accounts
* Privilege Escalation
* New Trusts
* Dormant Accounts

---

# Risk Indicators

Inactive Admins

Excessive Permissions

Privilege Accumulation

Service Account Exposure

Trust Misconfiguration

---

# Goal

Enable identity-first security visibility and governance.
