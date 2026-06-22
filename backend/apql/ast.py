"""Abstract Syntax Tree for APQL."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class FilterNode:
    field: str
    operator: str  # '=', '>=', '<=', '>', '<', '!=', 'IN', 'CONTAINS'
    value: str | float | int | bool | list[str | float | int | bool]

@dataclass(frozen=True)
class CompoundFilterNode:
    operator: str  # 'AND', 'OR'
    left: FilterNode | CompoundFilterNode
    right: FilterNode | CompoundFilterNode

@dataclass(frozen=True)
class SortNode:
    field: str
    direction: str  # 'ASC', 'DESC'

@dataclass(frozen=True)
class RelationshipNode:
    target_id: str
    depth: int = 1

@dataclass(frozen=True)
class QueryNode:
    entity: str  # 'ASSETS', 'SERVICES', 'IDENTITIES', 'DATASTORES', 'ZONES'
    filters: list[FilterNode | CompoundFilterNode] = field(default_factory=list)
    limit: int | None = None
    connected_to: RelationshipNode | None = None
    order_by: SortNode | None = None
