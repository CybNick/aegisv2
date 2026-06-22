"""Reporting schemas and types for Milestone 7.

Defines the supported report types and formats.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class ReportFormat(str, Enum):
    """Supported report output formats."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"

class ReportType(str, Enum):
    """Supported report types."""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    ASSET_INVENTORY = "asset_inventory"
    CRITICAL_ASSETS = "critical_assets"
    SENSITIVE_DATA = "sensitive_data"
    EXECUTIVE_ACTION_PLAN = "executive_action_plan"
    RISK_REMEDIATION = "risk_remediation"
    CRITICAL_FINDINGS = "critical_findings"
    OWNERSHIP = "ownership"
    EXECUTIVE_BOARD_REPORT = "executive_board_report"
    COMPLIANCE_REPORT = "compliance_report"
    RISK_TREND_REPORT = "risk_trend_report"
    GOVERNANCE_REPORT = "governance_report"
    AI_EXECUTIVE_SUMMARY = "ai_executive_summary"
    AI_RISK_NARRATIVE = "ai_risk_narrative"
    AI_COMPLIANCE_NARRATIVE = "ai_compliance_narrative"

class ReportResult(BaseModel):
    """The generic wrapper for an generated report."""
    report_type: ReportType
    format: ReportFormat
    as_of: float
    context: str
    content: str | dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
