"""Query Planner for APQL."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from backend.apql.ast import QueryNode

@dataclass
class PlanStep:
    name: str
    params: dict[str, Any]

class APQLPlanner:
    def __init__(self, ast: QueryNode):
        self.ast = ast
        
    def build_plan(self) -> list[PlanStep]:
        plan = []
        
        # 1. NodeScan
        # Maps ASSETS -> asset, SERVICES -> service, etc.
        kind_map = {
            "ASSETS": "ASSET",
            "SERVICES": "SERVICE",
            "IDENTITIES": "IDENTITY",
            "DATASTORES": "DATASTORE",
            "ZONES": "ZONE"
        }
        target_kind = kind_map.get(self.ast.entity)
        if not target_kind:
            raise ValueError(f"Unknown entity kind in AST: {self.ast.entity}")
            
        plan.append(PlanStep("NodeScan", {"kind": target_kind}))
        
        # 2. Relationship Filter (CONNECTED_TO)
        if self.ast.connected_to:
            plan.append(PlanStep("Traverse", {
                "target_id": self.ast.connected_to.target_id,
                "depth": self.ast.connected_to.depth
            }))
            
        # 3. Filters
        for f in self.ast.filters:
            plan.append(PlanStep("Filter", {"node": f}))
            
        # 4. Sort
        if self.ast.order_by:
            plan.append(PlanStep("Sort", {
                "field": self.ast.order_by.field,
                "direction": self.ast.order_by.direction
            }))
            
        # 5. Limit
        if self.ast.limit is not None:
            plan.append(PlanStep("Limit", {"limit": self.ast.limit}))
            
        return plan
