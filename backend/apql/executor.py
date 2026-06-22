"""Execution Engine for APQL."""

from __future__ import annotations
from typing import Any

from backend.analysis.query import GraphView
from backend.apql.planner import PlanStep

class APQLExecutor:
    def __init__(self, view: GraphView):
        self.view = view
        
    def execute(self, plan: list[PlanStep]) -> list[dict[str, Any]]:
        # 1. Start with empty working set
        working_set: set[str] = set()
        
        # We assume the first step is NodeScan
        scan_step = plan[0]
        if scan_step.name != "NodeScan":
            raise ValueError("First plan step must be NodeScan")
            
        target_kind = scan_step.params["kind"]
        
        # Populate working set
        for nid in self.view.live_node_ids():
            n = self.view.node(nid)
            if n and n.node_type.value == target_kind:
                working_set.add(nid)
                
        # 2. Process remaining steps pipeline
        for step in plan[1:]:
            if step.name == "Traverse":
                working_set = self._execute_traverse(working_set, step.params)
            elif step.name == "Filter":
                working_set = self._execute_filter(working_set, step.params)
            elif step.name == "Sort":
                # Sort step requires transitioning from set to list
                results = self._build_results(working_set)
                results = self._execute_sort(results, step.params)
                # Since limit usually follows sort, we just process limit and return early
                # But to maintain pipeline, we can just replace working set? No, order matters now.
                # Actually, wait. Sort implies returning a list. Let's just break out and do it outside.
                pass
                
        # If we didn't sort yet, we must convert to list now and sort by ID for determinism
        results = self._build_results(working_set)
        
        # Apply Sort if it exists in the plan
        sort_step = next((s for s in plan if s.name == "Sort"), None)
        if sort_step:
            results = self._execute_sort(results, sort_step.params)
        else:
            # Deterministic default sort by ID
            results.sort(key=lambda r: r["id"])
            
        # Apply Limit if it exists, otherwise cap at 1000
        limit_val = 1000
        limit_step = next((s for s in plan if s.name == "Limit"), None)
        if limit_step:
            limit_val = min(1000, limit_step.params["limit"])
            
        results = results[:limit_val]
            
        return results

    def _build_results(self, node_ids: set[str]) -> list[dict[str, Any]]:
        results = []
        for nid in node_ids:
            node = self.view.node(nid)
            state = self.view.node_state(nid)
            results.append({
                "id": nid,
                "type": node.node_type.value,
                "attributes": state.value,
                "confidence": state.confidence
            })
        return results

    def _execute_traverse(self, working_set: set[str], params: dict[str, Any]) -> set[str]:
        target_id = params["target_id"]
        max_depth = params["depth"]
        
        # BFS from target_id up to max_depth
        visited = {target_id}
        queue = [(target_id, 0)]
        
        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue
                
            # Neighbors (undirected traversal for CONNECTED_TO)
            neighbors = set()
            for e in self.view.out_edges(current):
                neighbors.add(e.dst)
            for e in self.view.in_edges(current):
                neighbors.add(e.src)
                
            for n in neighbors:
                if n not in visited:
                    visited.add(n)
                    queue.append((n, depth + 1))
                    
        # Exclude the target_id itself from the results unless explicitly requested
        visited.discard(target_id)
        # Intersect working set with visited
        return working_set.intersection(visited)

    def _execute_filter(self, working_set: set[str], params: dict[str, Any]) -> set[str]:
        node = params["node"]
        filtered = set()
        for nid in working_set:
            if self._evaluate_node(nid, node):
                filtered.add(nid)
        return filtered

    def _evaluate_node(self, nid: str, node: Any) -> bool:
        from backend.apql.ast import CompoundFilterNode, FilterNode
        
        if isinstance(node, CompoundFilterNode):
            left_val = self._evaluate_node(nid, node.left)
            right_val = self._evaluate_node(nid, node.right)
            if node.operator == "AND":
                return left_val and right_val
            elif node.operator == "OR":
                return left_val or right_val
            return False
            
        if isinstance(node, FilterNode):
            state = self.view.node_state(nid)
            field = node.field.lower()
            if field == "confidence":
                actual = state.confidence
            elif field == "id":
                actual = nid
            else:
                actual = state.value.get(field)
                
            if actual is None:
                return False
                
            return self._evaluate_condition(actual, node.operator, node.value)
            
        return False

    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        try:
            if operator == "=": return actual == expected
            if operator == "!=": return actual != expected
            if operator == ">": return float(actual) > float(expected)
            if operator == ">=": return float(actual) >= float(expected)
            if operator == "<": return float(actual) < float(expected)
            if operator == "<=": return float(actual) <= float(expected)
            if operator == "IN": return actual in expected
            if operator == "CONTAINS": return expected.lower() in str(actual).lower()
        except (ValueError, TypeError):
            return False
        return False

    def _execute_sort(self, results: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
        field = params["field"].lower()
        reverse = params["direction"].upper() == "DESC"
        
        def _sort_key(item: dict[str, Any]) -> tuple[Any, str]:
            if field == "confidence":
                val = item["confidence"]
            elif field == "id":
                val = item["id"]
            else:
                val = item["attributes"].get(field)
                
            # Handle mixed types by converting to string as fallback or sorting None down
            if val is None:
                return (0, str(val)) if reverse else (1, str(val))
                
            try:
                # Try numeric sort first
                return (0, float(val))
            except (ValueError, TypeError):
                # Fallback to string sort
                return (0, str(val))
                
        results.sort(key=_sort_key, reverse=reverse)
        return results
