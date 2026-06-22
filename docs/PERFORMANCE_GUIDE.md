# Aegis Performance Architecture Guide

As Aegis scales to ingest environments with over 100,000 nodes, the architecture leverages specific design patterns to ensure the UI remains instantly responsive.

## 1. Graph Virtualization (Lazy Loading)
**API:** `GET /api/v1/graph/subgraph`

Instead of loading the entire JSON graph representation into the browser (which crashes cytoscape.js past ~20k elements), the frontend relies on **subgraph virtualization**. 
When the user clicks on a node or searches for an asset, the backend executes a highly optimized Breadth-First Search (BFS), bounded by a configurable `depth` and `limit`, starting from the `center_node`. The user can progressively "Expand Depth" to explore neighborhoods.

## 2. Deterministic Intelligence Caching
**Module:** `backend.performance.cache_manager`

Generating Risk Scores, Compliance Mappings, and Advanced Intelligence over 100k nodes takes computational time.
Because Aegis uses an Append-Only Temporal Graph, we can reliably cache the output of these heavy engines. 
The Cache Manager generates a `graph_hash` based on the context, logical timestamp (`as_of`), live node count, and edge count. If a query requests data for a graph hash that has already been computed, it returns the cached result in sub-millisecond time.
When new events are appended, the graph hash naturally changes, instantly invalidating the cache and ensuring data is never stale.

## 3. Global Unified Search
Instead of traversing the frontend DOM, search is executed purely via `GET /api/v1/search`. The backend linearly scans the `GraphView` memory structure, matching against Node IDs and metadata properties simultaneously, delivering unified results across Assets, Risks, and Compliance instantly.
