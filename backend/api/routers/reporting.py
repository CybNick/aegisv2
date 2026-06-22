"""Reporting API router (doc ``21`` *Reporting APIs*).

Generates actionable reports in various formats.
"""

from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, Query, Depends
from backend.api.security import require_readonly

from backend.graph.model import DEFAULT_CONTEXT
from backend.api.dependencies import get_storage_layout
from backend.api.responses import success_response
from backend.api.schemas.common import ResponseEnvelope
from backend.reporting.schemas import ReportFormat, ReportType
from backend.api.services.reporting_service import ReportingService
from backend.storage.graph_store import PersistentGraphStore, StorageLayout

router = APIRouter(dependencies=[Depends(require_readonly)], prefix="/reports", tags=["reports"])

_CTX = Query(DEFAULT_CONTEXT, description="Context to scope the report to.")
_AS_OF = Query(None, description="Report as of this timestamp (latest if omitted).")

def get_reporting_service(layout: StorageLayout = Depends(get_storage_layout)) -> ReportingService:
    store = PersistentGraphStore(layout)
    return ReportingService(store)

ReportingServiceDep = Annotated[ReportingService, Depends(get_reporting_service)]

@router.get("/{report_type}", response_model=ResponseEnvelope, summary="Generate a report")
def generate_report(
    report_type: ReportType,
    service: ReportingServiceDep,
    format: ReportFormat = Query(ReportFormat.JSON, description="Output format"),
    context: str = _CTX,
    as_of: float | None = _AS_OF,
) -> dict:
    content, confidence, metadata = service.generate_report(
        report_type=report_type, fmt=format, context=context, as_of=as_of
    )
    return success_response(content, confidence=confidence, metadata=metadata)
