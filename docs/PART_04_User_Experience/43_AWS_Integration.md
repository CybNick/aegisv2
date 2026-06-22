# AWS Integration

Version: 1.0

---

# Purpose

Discover AWS infrastructure and identity relationships.

---

# Supported Services

EC2

VPC

IAM

RDS

S3

EKS

Lambda

Route53

Load Balancers

CloudTrail

Security Hub

Organizations

---

# Asset Discovery

Collect:

* Instance IDs
* Names
* Tags
* Regions
* Availability Zones
* IP Addresses
* Security Groups

---

# Identity Collection

Collect:

* Users
* Groups
* Roles
* Policies
* Trust Relationships

---

# Network Collection

Collect:

* VPCs
* Subnets
* Route Tables
* NAT Gateways
* Internet Gateways

---

# Data Storage Discovery

Collect:

* RDS
* DynamoDB
* S3

---

# Security Metadata

Collect:

* Security Hub Findings
* GuardDuty Metadata
* IAM Exposure Data

---

# Graph Mapping

AWS Resource → ASSET

IAM Role → IDENTITY

Policy → HAS_PERMISSION

VPC → ZONE

---

# Drift Detection

Monitor:

* New Resources
* Deleted Resources
* Policy Changes
* Permission Escalations

---

# Risk Indicators

Public Assets

Public Databases

Excessive Permissions

Unused Privileged Roles

Internet Exposure

---

# Goal

Provide complete AWS visibility and identity awareness.
