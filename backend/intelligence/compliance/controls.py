from enum import Enum
from pydantic import BaseModel
from typing import List

class Framework(str, Enum):
    CIS = "CIS"
    NIST = "NIST"
    ISO = "ISO 27001"
    SOC2 = "SOC 2"
    PCI = "PCI DSS"

class Control(BaseModel):
    framework: Framework
    id: str
    title: str
    description: str

class ControlFailure(BaseModel):
    control: Control
    reason: str
    evidence_nodes: List[str]
    recommendation_id: str | None = None
