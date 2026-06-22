from backend.analysis.query import GraphView

def classify_environment(view: GraphView, node_id: str) -> str:
    """Deterministically classify an asset's environment (Production, Staging, Development, Testing)."""
    node = view.node(node_id)
    if not node:
        return "Unknown"
        
    val = view.value_of(node_id)
    name = str(val.get("name", "")).lower()
    tags = val.get("tags", {})
    if isinstance(tags, dict):
        env_tag = str(tags.get("env", "")).lower() or str(tags.get("environment", "")).lower()
    else:
        env_tag = ""
        
    # Heuristic 1: Explicit Tags
    if env_tag in ["prod", "production"]:
        return "Production"
    elif env_tag in ["stage", "staging"]:
        return "Staging"
    elif env_tag in ["dev", "development"]:
        return "Development"
    elif env_tag in ["test", "testing"]:
        return "Testing"
        
    # Heuristic 2: Naming Conventions
    if "-prod" in name or "prod-" in name or "production" in name:
        return "Production"
    if "-stg" in name or "-stage" in name or "staging" in name:
        return "Staging"
    if "-dev" in name or "dev-" in name or "development" in name:
        return "Development"
    if "-test" in name or "test-" in name:
        return "Testing"
        
    # Heuristic 3: Inherit from upstream dependencies (if an app connects to a prod DB, it's probably prod)
    # This requires looking at what depends on it or what it connects to.
    # For now, default to Unknown.
    return "Unknown"
