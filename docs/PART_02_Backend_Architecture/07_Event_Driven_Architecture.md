# Event Driven Architecture

Version: 1.0

---

## Principle

Everything is an event.

No direct state mutations are allowed.

---

## Event Categories

### Discovery Events

* AssetDiscovered
* AssetUpdated
* AssetRemoved

### Service Events

* ServiceDetected
* ServiceChanged

### Identity Events

* IdentityObserved
* PermissionObserved

### Relationship Events

* RelationshipObserved
* RelationshipInferred

### Risk Events

* ExposureDetected
* RiskScoreChanged

### System Events

* ScanStarted
* ScanCompleted
* ConnectorSynced

---

## Event Structure

Every event contains:

* Event ID
* Event Type
* Timestamp
* Source
* Confidence
* Evidence
* Payload

---

## Immutability

Events cannot be modified.

Corrections generate new events.

---

## Event Flow

Source
→ Normalization
→ Validation
→ Event Creation
→ Graph Update
→ Analysis Trigger

---

## Benefits

* Full auditability
* Time travel support
* Historical reconstruction
* Explainable reasoning
