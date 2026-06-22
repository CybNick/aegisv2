from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class RecommendationCategory(str, Enum):
    EXPOSURE = "EXPOSURE"
    IDENTITY = "IDENTITY"
    DEPENDENCY = "DEPENDENCY"
    DRIFT = "DRIFT"
    MONITORING = "MONITORING"
    SENSITIVE_DATA = "SENSITIVE_DATA"
    CRITICAL_ASSET = "CRITICAL_ASSET"

class RecommendationSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Recommendation(BaseModel):
    id: str
    severity: RecommendationSeverity
    category: RecommendationCategory
    title: str
    description: str
    reason: List[str]
    actions: List[str]
    affected_nodes: List[str] = Field(default_factory=list)
