# 48_Kubernetes_Integration.md

Version: 1.0

---

# Purpose

Provide visibility into Kubernetes infrastructure, workloads, services, networking, and access controls.

---

# Supported Platforms

Kubernetes

Amazon EKS

Azure AKS

Google GKE

OpenShift

Rancher

---

# Resources Collected

Clusters

Namespaces

Nodes

Pods

Deployments

Services

Ingresses

ConfigMaps

Secrets Metadata

Persistent Volumes

RBAC Objects

---

# Cluster Discovery

Collect:

* Cluster Metadata
* Kubernetes Version
* Region
* Environment

---

# Workload Discovery

Collect:

* Deployments
* StatefulSets
* DaemonSets
* Jobs
* CronJobs

---

# Service Discovery

Collect:

* Internal Services
* Load Balancers
* Ingress Controllers
* Exposed Endpoints

---

# Identity Collection

Collect:

* Service Accounts
* Roles
* Role Bindings
* Cluster Roles
* Cluster Role Bindings

---

# Graph Mapping

Cluster → ZONE

Node → ASSET

Pod → SERVICE

Service Account → IDENTITY

Role Binding → HAS_PERMISSION

Ingress → EXPOSES

---

# Exposure Analysis

Identify:

Internet-Facing Services

Public Ingresses

Exposed APIs

Misconfigured Networking

---

# Risk Indicators

Cluster Admin Exposure

Over-Permissive RBAC

Public Workloads

Orphaned Resources

Excessive Privileges

---

# Drift Detection

New Workloads

Deleted Workloads

RBAC Changes

Network Exposure Changes

Namespace Changes

---

# Goal

Deliver complete Kubernetes visibility and governance.
