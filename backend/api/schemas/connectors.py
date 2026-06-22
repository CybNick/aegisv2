"""Pydantic schemas for the Connectors API."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")

class ConnectorCreateRequest(BaseModel):
    """Payload to register a new connector."""
    id: str = Field(..., description="Unique connector instance ID")
    type: str = Field(..., description="The type of connector (e.g., 'mock', 'csv')")
    enabled: bool = Field(default=True)
    params: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("id")
    def validate_id(cls, v: str) -> str:
        if not ID_REGEX.match(v):
            raise ValueError("Connector ID must match ^[a-zA-Z0-9_-]+$")
        return v
