# Threat Model

## Objective

Protect Aegis itself.

---

## Threat Categories

### Unauthorized Access

Risks:

* Stolen credentials
* Session hijacking

Mitigations:

* MFA
* Session expiration

---

### Data Leakage

Risks:

* Unauthorized exports
* Misconfigured storage

Mitigations:

* Encryption
* RBAC
* Audit Logging

---

### Supply Chain Risk

Risks:

* Malicious dependency

Mitigations:

* Dependency scanning
* SBOM generation

---

### Privilege Escalation

Risks:

* Role abuse

Mitigations:

* Least privilege
* Access reviews

---

### Configuration Tampering

Risks:

* Unauthorized changes

Mitigations:

* Immutable audit trail
* Change approvals
