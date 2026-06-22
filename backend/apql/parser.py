"""Parser for APQL."""

from __future__ import annotations
import shlex

from backend.apql.ast import QueryNode, FilterNode, SortNode, RelationshipNode, CompoundFilterNode

class APQLSyntaxError(Exception):
    """Raised on APQL syntax errors."""
    pass

class APQLParser:
    def __init__(self, query: str):
        self.query = query
        try:
            # Preprocess to separate brackets and commas for IN array parsing
            q = query.replace('[', ' [ ').replace(']', ' ] ').replace(',', ' , ')
            self.tokens = shlex.split(q)
        except ValueError as e:
            raise APQLSyntaxError(f"Tokenization error: {str(e)}")
        
        self.pos = 0
    
    def peek(self) -> str | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def consume(self) -> str:
        if self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            self.pos += 1
            return tok
        raise APQLSyntaxError("Unexpected end of query")
    
    def match(self, expected: str) -> bool:
        tok = self.peek()
        if tok and tok.upper() == expected.upper():
            self.consume()
            return True
        return False
    
    def expect(self, expected: str):
        if not self.match(expected):
            tok = self.peek()
            raise APQLSyntaxError(f"Expected '{expected}', got '{tok}'")
            
    def _parse_value(self, val_str: str) -> str | float | int | bool:
        if val_str.lower() == "true":
            return True
        if val_str.lower() == "false":
            return False
        try:
            if "." in val_str:
                return float(val_str)
            return int(val_str)
        except ValueError:
            return val_str

    def _parse_array(self) -> list[str | float | int | bool]:
        self.expect("[")
        items = []
        while self.peek() and self.peek() != "]":
            tok = self.consume()
            if tok == ",":
                continue
            items.append(self._parse_value(tok))
        self.expect("]")
        return items

    def _parse_condition(self) -> FilterNode:
        field = self.consume()
        op = self.consume()
        valid_ops = {"=", ">=", "<=", ">", "<", "!=", "IN", "CONTAINS"}
        if op.upper() not in valid_ops:
            raise APQLSyntaxError(f"Invalid operator: {op}")
            
        if op.upper() == "IN":
            val = self._parse_array()
        else:
            val_str = self.consume()
            val = self._parse_value(val_str)
            
        return FilterNode(field=field, operator=op.upper(), value=val)

    def parse(self) -> QueryNode:
        if not self.peek():
            raise APQLSyntaxError("Empty query")
            
        # Parse FIND / SHOW
        if self.match("FIND") or self.match("SHOW"):
            pass
        else:
            raise APQLSyntaxError(f"Query must start with FIND or SHOW, got {self.peek()}")
            
        entity = self.consume().upper()
        if entity not in {"ASSETS", "SERVICES", "IDENTITIES", "DATASTORES", "ZONES"}:
            raise APQLSyntaxError(f"Unknown entity type: {entity}")
            
        filters = []
        limit = None
        order_by = None
        connected_to = None
        
        while self.peek():
            tok = self.peek().upper()
            
            if tok == "WHERE":
                self.consume()
                filter_node = self._parse_condition()
                
                # Check for AND / OR compound logic
                while self.peek() and self.peek().upper() in ("AND", "OR"):
                    op = self.consume().upper()
                    next_filter = self._parse_condition()
                    filter_node = CompoundFilterNode(operator=op, left=filter_node, right=next_filter)
                    
                filters.append(filter_node)
                
            elif tok == "WITH":
                self.consume()
                flag = self.consume()
                filters.append(FilterNode(field=flag.lower(), operator="=", value=True))
                
            elif tok == "ORDER":
                self.consume()
                self.expect("BY")
                field = self.consume()
                direction = "ASC"
                if self.peek() and self.peek().upper() in ("ASC", "DESC"):
                    direction = self.consume().upper()
                order_by = SortNode(field=field, direction=direction)
                
            elif tok == "LIMIT":
                self.consume()
                val = self.consume()
                try:
                    limit = int(val)
                except ValueError:
                    raise APQLSyntaxError(f"LIMIT requires an integer, got: {val}")
                    
            elif tok == "CONNECTED_TO":
                self.consume()
                target_id = self.consume()
                depth = 1
                if self.match("DEPTH"):
                    d_val = self.consume()
                    try:
                        depth = int(d_val)
                        if depth > 5:
                            raise APQLSyntaxError(f"DEPTH cannot exceed 5, got: {depth}")
                    except ValueError:
                        raise APQLSyntaxError(f"DEPTH requires an integer, got: {d_val}")
                connected_to = RelationshipNode(target_id=target_id, depth=depth)
                
            else:
                raise APQLSyntaxError(f"Unexpected token: {tok}")

        return QueryNode(
            entity=entity,
            filters=filters,
            limit=limit,
            connected_to=connected_to,
            order_by=order_by
        )
