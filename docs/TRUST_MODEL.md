# Aegis Trust & Evidence Model

Aegis is built on an absolute principle: **Zero Hallucination. 100% Explainable Determinism.**

## 1. Local-First Architecture
All data stays on the user's local machine or designated local server. There are no external cloud processing dependencies. 
If the host system is air-gapped, Aegis functions with 100% of its capabilities (with the exception of API-based enterprise connectors like AWS, which naturally require outbound access to the target cloud).

## 2. Deterministic Graph Store
All findings in Aegis originate from the `GraphView`.
The Graph is append-only. 
Data mutations are not destructive. This provides an immutable Evidence Chain. 
Every asset, risk score, and compliance violation can be mathematically traced back to the exact JSON event payload produced by a Connector at a specific timestamp.

## 3. Natural Language Intelligence without AI Hallucinations
Aegis's "AI Assistant" translates human input into strict APQL queries. It then retrieves deterministic results from the graph and formats them into readable summaries. 
**No generative AI is used to invent facts.** If Aegis says a server is exposed, it's because there is a mathematically provable edge connecting it to the `internet` node.

## 4. Confidence Scores
Because Aegis relies on objective facts (e.g. "Does port 443 point to this IP?"), the baseline confidence score for intelligence outputs is **1.0 (100%)**. 
Confidence scores may dynamically degrade only if the underlying Connector explicitly flags a piece of metadata as heuristic or uncertain.
