from fastapi import APIRouter, Depends, Query, HTTPException
from backend.api.schemas.responses import ResponseEnvelope, success_response
from backend.api.dependencies import get_graph_layout
from backend.storage.graph_store import PersistentGraphStore
from backend.analysis.query import QueryEngine

from backend.api.security import require_readonly
router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/graph", tags=["graph_virtual"])

_CTX = Query("default", description="Graph context")
_AS_OF = Query(None, description="Optional logical timestamp")

@router.get("/subgraph", response_model=ResponseEnvelope, summary="Virtual Graph API")
def get_subgraph(
    center_node: str = Query(..., description="Node ID to center the subgraph on"),
    depth: int = Query(1, description="Depth of traversal"),
    limit: int = Query(100, description="Max nodes to return"),
    layout=Depends(get_graph_layout),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    store = PersistentGraphStore(layout)
    graph = store.load_graph()
    query_engine = QueryEngine(graph)
    view = query_engine.view(context=context, as_of=as_of)

    if center_node not in view.live_node_ids():
        raise HTTPException(status_code=404, detail="Center node not found")

    live = set(view.live_node_ids())
    visited = set([center_node])
    queue = [(center_node, 0)]

    nodes = []
    edges = []
    seen_edges = set()

    # Breadth-first expansion over live edges around the center node.
    while queue and len(nodes) < limit:
        curr, d = queue.pop(0)

        ntype = view.node_type(curr)
        nodes.append({
            "id": curr,
            "type": ntype.value if ntype else "UNKNOWN",
            "properties": view.node_properties(curr),
        })

        if d < depth:
            for edge in view.out_edges(curr) + view.in_edges(curr):
                neighbor = edge.dst if edge.src == curr else edge.src
                if neighbor not in live:
                    continue
                if edge.id not in seen_edges:
                    seen_edges.add(edge.id)
                    edges.append({
                        "id": edge.id,
                        "source": edge.src,
                        "target": edge.dst,
                        "type": edge.edge_type.value,
                        "properties": {},
                    })
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, d + 1))

    return success_response({
        "nodes": nodes,
        "edges": edges,
    })
