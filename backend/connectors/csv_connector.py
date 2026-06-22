"""CSV connector for manual asset importation."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from backend.connectors.base import BaseConnector
from backend.connectors.schemas import ConnectorResult
from backend.graph.schemas import AssetObservation, AssetRef, ServiceObservation, ZoneObservation

class CSVConnector(BaseConnector):
    """Imports assets and services from a CSV file."""
    
    @property
    def connector_type(self) -> str:
        return "csv"

    def __init__(self, csv_data: str, **kwargs: Any) -> None:
        self.csv_data = csv_data

    def collect(self, observed_at: float, context: str = "default") -> ConnectorResult:
        """Parse CSV and emit observations."""
        observations = []
        skipped = 0
        parsed = 0
        
        # Read the raw string
        f = StringIO(self.csv_data.strip())
        reader = csv.DictReader(f)
        
        if not reader.fieldnames:
            return ConnectorResult("csv", observed_at, tuple(), {"error": "Empty or invalid CSV"})
            
        # Expected columns: hostname, ip, zone, service, port, owner
        for row_idx, row in enumerate(reader, start=1):
            # Normalize keys to lower case and strip whitespace
            clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k and v}
            
            hostname = clean_row.get("hostname")
            ip = clean_row.get("ip")
            
            if not hostname and not ip:
                skipped += 1
                continue
                
            parsed += 1
            
            # 1. Zone
            zone_name = clean_row.get("zone")
            if zone_name:
                observations.append(
                    ZoneObservation(
                        name=zone_name,
                        source=self.connector_type,
                        observed_at=observed_at,
                        evidence=(f"csv:zone:{zone_name}",),
                        context=context,
                    )
                )
            
            # 2. Asset
            asset_ref = AssetRef(
                hostname=hostname if hostname else None,
                ip=ip if ip else None
            )
            
            attributes = {}
            if "owner" in clean_row:
                attributes["owner"] = clean_row["owner"]
                
            evidence_str = f"csv:asset:{hostname or ip}"
            observations.append(
                AssetObservation(
                    ref=asset_ref,
                    source=self.connector_type,
                    observed_at=observed_at,
                    evidence=(evidence_str,),
                    attributes=attributes,
                    context=context,
                )
            )
            
            # 3. Service
            service_name = clean_row.get("service")
            port_str = clean_row.get("port")
            if service_name and port_str and port_str.isdigit():
                port = int(port_str)
                observations.append(
                    ServiceObservation(
                        host=asset_ref,
                        port=port,
                        source=self.connector_type,
                        observed_at=observed_at,
                        evidence=(f"csv:service:{hostname or ip}:{port}",),
                        metadata={"name": service_name},
                        context=context,
                    )
                )
                
        # Sort observations deterministically before returning
        # We sort by the hash of their dump so that row order doesn't matter.
        def _sort_key(obs):
            return str(obs)
            
        sorted_obs = sorted(observations, key=_sort_key)
                
        return ConnectorResult(
            connector_id="csv_import",
            observed_at=observed_at,
            observations=tuple(sorted_obs),
            metadata={"parsed_rows": parsed, "skipped_rows": skipped}
        )
