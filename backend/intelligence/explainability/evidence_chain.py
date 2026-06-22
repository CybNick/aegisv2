from typing import List, Optional
from pydantic import BaseModel

class EvidenceStep(BaseModel):
    node_id: Optional[str] = None
    node_name: Optional[str] = None
    node_type: Optional[str] = None
    edge_type: Optional[str] = None
    description: str

class EvidenceChain(BaseModel):
    """Represents a deterministic path of logic or graph traversal."""
    description: str
    steps: List[EvidenceStep]
    confidence: float = 1.0  # Aegis is deterministic, so it's 1.0 unless heuristically degraded
