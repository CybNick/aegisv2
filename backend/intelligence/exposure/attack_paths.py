from typing import Any, Dict, List
from collections import deque
from backend.analysis.query import GraphView

def calculate_shortest_path(view: GraphView, source_id: str, target_id: str) -> Dict[str, Any]:
    """Calculate the shortest path between two nodes using BFS."""
    
    if source_id not in view.live_node_ids() or target_id not in view.live_node_ids():
        return {"error": "Source or Target node not found"}
        
    # BFS Queue: (current_node_id, path_of_nodes, path_of_edges)
    queue = deque([(source_id, [source_id], [])])
    visited = {source_id}
    
    while queue:
        curr_id, node_path, edge_path = queue.popleft()
        
        if curr_id == target_id:
            # Reconstruct severity based on edge confidence
            # Lower confidence -> Higher difficulty -> Lower severity
            min_confidence = 1.0
            for e in edge_path:
                state = view.edge_state(e)
                if state and state.confidence < min_confidence:
                    min_confidence = state.confidence
                    
            severity = "CRITICAL"
            if min_confidence < 0.5:
                severity = "LOW"
            elif min_confidence < 0.8:
                severity = "MEDIUM"
            elif min_confidence < 0.95:
                severity = "HIGH"
                
            return {
                "source": source_id,
                "target": target_id,
                "nodes": node_path,
                "edges": edge_path,
                "distance": len(edge_path),
                "severity": severity,
                "score": int(min_confidence * 100)
            }
            
        # Traverse outgoing edges
        for edge in view.out_edges(curr_id):
            if edge.dst not in visited:
                visited.add(edge.dst)
                queue.append((edge.dst, node_path + [edge.dst], edge_path + [edge.id]))
                
    return {"error": "No path found between source and target"}

def get_all_attack_paths(view: GraphView, source_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
    """Find all paths from a source to highly exposed targets up to a depth."""
    if source_id not in view.live_node_ids():
        return []
        
    paths = []
    queue = deque([(source_id, [source_id], [])])
    
    while queue:
        curr_id, node_path, edge_path = queue.popleft()
        
        if len(node_path) > max_depth:
            continue
            
        if len(node_path) > 1:
            paths.append({
                "source": source_id,
                "target": curr_id,
                "nodes": node_path,
                "edges": edge_path,
                "distance": len(edge_path)
            })
            
        for edge in view.out_edges(curr_id):
            if edge.dst not in node_path:  # Prevent cycles
                queue.append((edge.dst, node_path + [edge.dst], edge_path + [edge.id]))
                
    return paths
