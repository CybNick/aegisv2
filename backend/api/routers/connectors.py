"""Connectors router for API Layer."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from backend.api.security import require_admin

from backend.api.dependencies import ConnectorServiceDep
from backend.api.responses import success_response, error_response
from backend.api.schemas.connectors import ConnectorCreateRequest

router = APIRouter(dependencies=[Depends(require_admin)], prefix="/connectors", tags=["connectors"])

@router.get("/")
async def list_connectors(service: ConnectorServiceDep) -> dict[str, Any]:
    """List all registered connectors and their states."""
    data = service.list_connectors()
    return success_response(data)

@router.get("/{instance_id}")
async def get_connector(instance_id: str, service: ConnectorServiceDep) -> dict[str, Any]:
    """Get a specific connector."""
    data = service.get_connector_info(instance_id)
    if not data:
        return error_response(error_code="NOT_FOUND", message=f"Connector '{instance_id}' not found")
    return success_response(data)

@router.post("/")
async def add_connector(
    req: ConnectorCreateRequest,
    service: ConnectorServiceDep
) -> dict[str, Any]:
    """Register a new connector instance."""
    try:
        service.add_connector(req.id, req.type, req.enabled, req.params)
        return success_response({"id": req.id})
    except ValueError as e:
        return error_response(error_code="CONFLICT", message=str(e))

@router.delete("/{instance_id}")
async def delete_connector(
    instance_id: str,
    service: ConnectorServiceDep
) -> dict[str, Any]:
    """Delete a connector instance."""
    try:
        service.delete_connector(instance_id)
        return success_response({"deleted": instance_id})
    except ValueError as e:
        return error_response(error_code="NOT_FOUND", message=str(e))

@router.post("/{instance_id}/sync")
async def sync_connector(
    instance_id: str,
    service: ConnectorServiceDep
) -> dict[str, Any]:
    """Manually trigger a connector run and return the sync stats."""
    try:
        data = service.sync_connector(instance_id)
        return success_response(data)
    except ValueError as e:
        return error_response(error_code="NOT_FOUND", message=str(e))
    except Exception as e:
        return error_response(error_code="INTERNAL_ERROR", message=str(e))

@router.post("/{instance_id}/validate")
async def validate_connector(
    instance_id: str,
    service: ConnectorServiceDep
) -> dict[str, Any]:
    """Validate a connector's configuration."""
    try:
        data = service.validate_connector(instance_id)
        return success_response(data)
    except ValueError as e:
        return error_response(error_code="NOT_FOUND", message=str(e))

@router.get("/{instance_id}/history")
async def get_connector_history(
    instance_id: str,
    service: ConnectorServiceDep
) -> dict[str, Any]:
    """Get the sync history for a connector."""
    data = service.get_connector_history(instance_id)
    return success_response({"history": data})

@router.get("/{instance_id}/status")
async def get_connector_status(
    instance_id: str,
    service: ConnectorServiceDep
) -> dict[str, Any]:
    """Get the current status of a connector."""
    data = service.get_connector_info(instance_id)
    if not data:
        return error_response(error_code="NOT_FOUND", message=f"Connector '{instance_id}' not found")
    return success_response(data)
