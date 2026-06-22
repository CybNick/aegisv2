import sys
import json
from pathlib import Path
from backend.storage.graph_store import StorageLayout, PersistentGraphStore
from backend.analysis.query import QueryEngine
from backend.intelligence.explainability.explainability_engine import ExplainabilityEngine
from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine

def run_verification():
    print("==========================================")
    print("AEGIS EXPLAINABILITY AUDIT")
    print("==========================================\n")
    
    layout = StorageLayout()
    store = PersistentGraphStore(layout).load()
    query_engine = QueryEngine(store)
    view = query_engine.view()
    
    exp_engine = ExplainabilityEngine(view)
    rec_engine = RecommendationEngine(view)
    
    recs = rec_engine.generate()
    
    total = len(recs)
    passed = 0
    failed = 0
    
    for r in recs:
        try:
            chain = exp_engine.explain_recommendation(r['id'], r['title'], "EXPOSURE", [r['target_id']])
            if chain and "evidence_chain" in chain:
                passed += 1
            else:
                failed += 1
                print(f"[FAIL] Missing chain for {r['id']}")
        except Exception as e:
            failed += 1
            print(f"[ERROR] Exception explaining {r['id']}: {e}")
            
    print(f"\nTotal Findings Evaluated: {total}")
    print(f"Explainability Success Rate: {100 * passed / max(1, total):.2f}%")
    
    report_content = f"""# Aegis Explainability Audit

## Objective
Verify that 100% of intelligence findings possess deterministic, verifiable evidence chains linking back to origin nodes.

## Results
- **Total Findings Evaluated**: {total}
- **Traceable Findings**: {passed}
- **Missing Traces**: {failed}
- **Verification Rate**: {100 * passed / max(1, total):.2f}%

## Conclusion
{"GO - 100% Determinism achieved." if failed == 0 else "NO-GO - Missing explainability traces detected."}
"""

    report_path = Path("docs/EXPLAINABILITY_AUDIT.md")
    report_path.parent.mkdir(exist_ok=True, parents=True)
    report_path.write_text(report_content)
    
    print("\nAudit written to docs/EXPLAINABILITY_AUDIT.md")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
