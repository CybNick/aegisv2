import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from backend.storage.graph_store import StorageLayout
from backend.storage.graph_store import PersistentGraphStore
from backend.analysis.query import QueryEngine, GraphView
from backend.analysis.risk import RiskAnalyzer
from backend.graph.model import Node, StateVersion
from backend.intelligence.compliance.compliance_engine import ComplianceEngine

@dataclass
class ChangeEvent:
    type: str
    target_id: str
    timestamp: float
    confidence: float
    details: Dict[str, Any]

class ChangeDetector:
    def __init__(self, layout: StorageLayout):
        self._layout = layout
        self._store = PersistentGraphStore(layout).load()
        self._risk_analyzer = RiskAnalyzer()

    def detect_changes(self, prev_time: float, curr_time: float) -> List[ChangeEvent]:
        if prev_time >= curr_time:
            return []

        # Re-initialize query engine to catch latest store updates
        self._store = PersistentGraphStore(self._layout).load()
        query_engine = QueryEngine(self._store)

        prev_view = query_engine.view(as_of=prev_time)
        curr_view = query_engine.view(as_of=curr_time)

        changes: List[ChangeEvent] = []
        
        prev_nodes = {nid: (prev_view.node(nid), prev_view.node_state(nid)) for nid in prev_view.live_node_ids()}
        curr_nodes = {nid: (curr_view.node(nid), curr_view.node_state(nid)) for nid in curr_view.live_node_ids()}

        # Analyze risk across the board
        prev_risks = {r.entity_id: r for r in self._risk_analyzer.analyze(prev_view)}
        curr_risks = {r.entity_id: r for r in self._risk_analyzer.analyze(curr_view)}

        # Detect node additions and removals
        for nid, (node, state) in curr_nodes.items():
            if nid not in prev_nodes:
                changes.append(ChangeEvent(
                    type=f"NEW_{node.node_type.value}",
                    target_id=nid,
                    timestamp=curr_time,
                    confidence=state.confidence,
                    details={"name": state.value.get("name", nid)}
                ))
            else:
                # Check Risk Changes
                prev_risk = prev_risks.get(nid)
                curr_risk = curr_risks.get(nid)
                
                prev_score = prev_risk.score if prev_risk else 0
                curr_score = curr_risk.score if curr_risk else 0

                if curr_score > prev_score:
                    changes.append(ChangeEvent(
                        type="RISK_INCREASE",
                        target_id=nid,
                        timestamp=curr_time,
                        confidence=state.confidence,
                        details={"old_score": prev_score, "new_score": curr_score}
                    ))
                elif curr_score < prev_score:
                    changes.append(ChangeEvent(
                        type="RISK_DECREASE",
                        target_id=nid,
                        timestamp=curr_time,
                        confidence=state.confidence,
                        details={"old_score": prev_score, "new_score": curr_score}
                    ))

        for nid, (node, state) in prev_nodes.items():
            if nid not in curr_nodes:
                changes.append(ChangeEvent(
                    type=f"REMOVED_{node.node_type.value}",
                    target_id=nid,
                    timestamp=curr_time,
                    confidence=state.confidence,
                    details={"name": state.value.get("name", nid)}
                ))

        # We can also detect EDGE changes (e.g. NEW_EXPOSURE)
        prev_edges = {e.id: (e, prev_view.edge_state(e.id)) for e in prev_view.live_edges()}
        curr_edges = {e.id: (e, curr_view.edge_state(e.id)) for e in curr_view.live_edges()}

        for eid, (edge, state) in curr_edges.items():
            if eid not in prev_edges:
                if edge.edge_type.value == "EXPOSED_TO":
                    dst_node = curr_view.node(edge.dst)
                    src_node = curr_view.node(edge.src)
                    
                    if edge.dst == "internet":
                        changes.append(ChangeEvent(
                            type="NEW_INTERNET_PATH",
                            target_id=edge.src,
                            timestamp=curr_time,
                            confidence=state.confidence,
                            details={"exposed_to": edge.dst}
                        ))
                    elif src_node and src_node.node_type.value == "SERVICE":
                        changes.append(ChangeEvent(
                            type="NEW_EXPOSED_SERVICE",
                            target_id=edge.src,
                            timestamp=curr_time,
                            confidence=state.confidence,
                            details={"exposed_to": edge.dst}
                        ))
                    else:
                        changes.append(ChangeEvent(
                            type="NEW_EXPOSURE",
                            target_id=edge.src,
                            timestamp=curr_time,
                            confidence=state.confidence,
                            details={"exposed_to": edge.dst}
                        ))
                        
                elif edge.edge_type.value == "HAS_PRIVILEGE":
                    changes.append(ChangeEvent(
                        type="PRIVILEGE_ESCALATION",
                        target_id=edge.src,
                        timestamp=curr_time,
                        confidence=state.confidence,
                        details={"privilege_on": edge.dst}
                    ))
                
                elif edge.edge_type.value == "OWNED_BY":
                    changes.append(ChangeEvent(
                        type="OWNERSHIP_DRIFT",
                        target_id=edge.src,
                        timestamp=curr_time,
                        confidence=state.confidence,
                        details={"new_owner": edge.dst}
                    ))
                    
        # Check Compliance Failure
        prev_comp = ComplianceEngine(prev_view).generate()
        curr_comp = ComplianceEngine(curr_view).generate()
        
        for fw, curr_data in curr_comp.get("frameworks", {}).items():
            prev_data = prev_comp.get("frameworks", {}).get(fw, {})
            prev_score = prev_data.get("score", 100)
            curr_score = curr_data.get("score", 100)
            
            if curr_score < prev_score:
                changes.append(ChangeEvent(
                    type="COMPLIANCE_FAILURE",
                    target_id="global",
                    timestamp=curr_time,
                    confidence=1.0,
                    details={"framework": fw, "old_score": prev_score, "new_score": curr_score}
                ))

        return changes
