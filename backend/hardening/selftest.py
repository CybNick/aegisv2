"""Master Hardening Selftest.

Runs M7.6 Regression tests, then falls back to M1-M7.5 Validation tests.
"""

from __future__ import annotations
import sys
import importlib

def run_all() -> None:
    print("Running M7.6 Hardening Regressions...")
    import backend.hardening.regression_tests as regressions
    try:
        assert regressions.test_snapshot_traversal(), "Path Traversal Test Failed"
        print("[PASS] Path Traversal Validation")
        assert regressions.test_html_xss(), "HTML XSS Test Failed"
        print("[PASS] HTML XSS Sanitization")
        assert regressions.test_evidence_ordering(), "Evidence Ordering Test Failed"
        print("[PASS] Evidence Ordering Determinism")
        assert regressions.test_ghost_edges(), "Ghost Edges Test Failed"
        print("[PASS] Ghost Edge Propagation Isolation")
    except Exception as e:
        print(f"M7.6 REGRESSION FAILURE: {e}")
        sys.exit(1)
        
    print("\nRunning M1-M7.5 Core Verification Suite...")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "backend.verification.selftest"])
    if result.returncode != 0:
        print("M1-M7.5 REGRESSION FAILURE")
        sys.exit(result.returncode)

if __name__ == "__main__":
    run_all()
