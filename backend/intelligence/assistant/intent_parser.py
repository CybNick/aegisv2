from enum import Enum
import re

class IntentCategory(str, Enum):
    EXPOSURE = "EXPOSURE"
    RISK = "RISK"
    ASSET = "ASSET"
    DEPENDENCY = "DEPENDENCY"
    COMPLIANCE = "COMPLIANCE"
    EXECUTIVE = "EXECUTIVE"
    TREND = "TREND"
    UNKNOWN = "UNKNOWN"

class IntentParser:
    """Deterministic keyword/pattern parser for natural language."""
    
    PATTERNS = {
        IntentCategory.EXPOSURE: [
            r"exposed.*internet", r"public.*database", r"externally reachable",
            r"exposed.*asset", r"internet reachable", r"publicly accessible"
        ],
        IntentCategory.RISK: [
            r"highest risk", r"most dangerous", r"critical risk",
            r"risk.*increasing", r"top risk"
        ],
        IntentCategory.ASSET: [
            r"production asset", r"sensitive data", r"who owns",
            r"asset.*contain", r"show.*asset"
        ],
        IntentCategory.DEPENDENCY: [
            r"depends on", r"if.*fails", r"what breaks", r"blast radius"
        ],
        IntentCategory.COMPLIANCE: [
            r"compliant", r"pci", r"controls.*failing", r"governance",
            r"compliance"
        ],
        IntentCategory.TREND: [
            r"what changed", r"risk.*week", r"risk.*month", r"trend"
        ],
        IntentCategory.EXECUTIVE: [
            r"fix first", r"summarize", r"executive summary", r"biggest problem",
            r"prioritize", r"leadership"
        ]
    }
    
    @classmethod
    def parse(cls, text: str) -> IntentCategory:
        text_lower = text.lower()
        
        # We find the intent that has the earliest/strongest match.
        # A simple approach: first match wins based on ordered checks or just standard loops.
        # Because we want a deterministic map, we'll just check all and return the first matched category.
        
        for category, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return category
                    
        return IntentCategory.UNKNOWN
