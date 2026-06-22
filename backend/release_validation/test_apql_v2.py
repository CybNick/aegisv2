from backend.apql.parser import APQLParser
from backend.apql.planner import APQLPlanner
from backend.apql.ast import CompoundFilterNode, FilterNode
import pytest

def test_apql_and():
    q = 'FIND ASSETS WHERE risk > 5 AND exposure = "internet"'
    ast = APQLParser(q).parse()
    assert len(ast.filters) == 1
    root_filter = ast.filters[0]
    assert isinstance(root_filter, CompoundFilterNode)
    assert root_filter.operator == "AND"
    assert root_filter.left.field == "risk"
    assert root_filter.right.value == "internet"

def test_apql_or():
    q = 'FIND SERVICES WHERE criticality = "high" OR exposure = "internet"'
    ast = APQLParser(q).parse()
    assert len(ast.filters) == 1
    root_filter = ast.filters[0]
    assert isinstance(root_filter, CompoundFilterNode)
    assert root_filter.operator == "OR"
    assert root_filter.left.field == "criticality"
    assert root_filter.right.field == "exposure"

def test_apql_in():
    q = 'FIND ASSETS WHERE environment IN ["prod", "stage"]'
    ast = APQLParser(q).parse()
    assert len(ast.filters) == 1
    f = ast.filters[0]
    assert isinstance(f, FilterNode)
    assert f.operator == "IN"
    assert f.value == ["prod", "stage"]

def test_apql_depth_limit():
    q_valid = 'FIND ASSETS CONNECTED_TO "db" DEPTH 5'
    ast = APQLParser(q_valid).parse()
    assert ast.connected_to.depth == 5
    
    q_invalid = 'FIND ASSETS CONNECTED_TO "db" DEPTH 6'
    with pytest.raises(Exception, match="DEPTH cannot exceed 5"):
        APQLParser(q_invalid).parse()
