"""Retention management and integrity validation for Aegis CCEIP (Milestone 5).

Provides:

* :class:`RetentionPolicy` — the five documented retention tiers (7, 30, 90,
  365 days, and FOREVER).
* :class:`RetentionManager` — policy-based archival of expired events and old
  snapshots. Only moves data to archive directories; never deletes active state.
* :class:`IntegrityValidator` — validates hash consistency, serialization
  integrity, schema version, and structural soundness across all storage tiers.
* :class:`IntegrityReport` / :class:`RetentionReport` — immutable result objects.

Design rules (docs ``20``, ``67``):

* No deletion of active state — only archival management.
* Deterministic policy execution.
* Active graph and current checkpoint are never touched.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

from backend.graph.model import SCHEMA_VERSION, canonical_dumps
from backend.graph.store import GraphStore
from backend.storage.graph_store import (
    PersistentGraphStore,
    StorageLayout,
    atomic_write_text,
    read_text,
    sha256_hex,
)


# --------------------------------------------------------------------------- #
# Retention policy (doc 67)                                                    #
# --------------------------------------------------------------------------- #

class RetentionPolicy(IntEnum):
    """Retention tiers — the number of days before archival.

    ``FOREVER`` (0) means data is never archived.
    """

    DAYS_7 = 7
    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_365 = 365
    FOREVER = 0


# --------------------------------------------------------------------------- #
# Result objects                                                               #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class RetentionReport:
    """Result of a retention policy execution."""

    archived_count: int
    remaining_count: int
    archive_path: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "archived_count": self.archived_count,
            "remaining_count": self.remaining_count,
            "archive_path": self.archive_path,
        }


@dataclass(frozen=True)
class IntegrityReport:
    """Result of an integrity validation check."""

    valid: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    hashes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "hashes": dict(self.hashes),
        }


# --------------------------------------------------------------------------- #
# RetentionManager                                                             #
# --------------------------------------------------------------------------- #

class RetentionManager:
    """Policy-based archival management (docs ``20``, ``67``).

    Moves expired data to archive directories. Never deletes active graph
    state or the current checkpoint. ``FOREVER`` policy skips all archival.
    """

    def __init__(self, layout: StorageLayout) -> None:
        self._layout = layout

    @property
    def layout(self) -> StorageLayout:
        return self._layout

    def apply_event_retention(
        self,
        policy: RetentionPolicy,
        now: float,
    ) -> RetentionReport:
        """Archive events older than ``now - policy`` days.

        Events with ``timestamp < cutoff`` are moved from ``events.jsonl`` to
        ``events/archive/events_<cutoff>.jsonl``. The FOREVER policy is a no-op.

        Args:
            policy: Retention tier.
            now: Current logical timestamp (seconds since epoch).

        Returns:
            Report of what was archived.
        """
        if policy is RetentionPolicy.FOREVER:
            count = self._count_events()
            return RetentionReport(
                archived_count=0,
                remaining_count=count,
                archive_path=None,
            )

        cutoff = now - (policy.value * 86400)  # days → seconds
        events_path = self._layout.events_jsonl
        if not events_path.exists():
            return RetentionReport(0, 0, None)

        keep: list[str] = []
        archive: list[str] = []

        with open(events_path, "r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    ts = data.get("timestamp", 0)
                    if ts < cutoff:
                        archive.append(stripped + "\n")
                    else:
                        keep.append(stripped + "\n")
                except (json.JSONDecodeError, KeyError):
                    keep.append(stripped + "\n")  # preserve unparseable lines

        if not archive:
            return RetentionReport(0, len(keep), None)

        # Write archived events.
        archive_dir = self._layout.events_archive_dir
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_name = f"events_{int(cutoff)}.jsonl"
        archive_path = archive_dir / archive_name
        atomic_write_text(archive_path, "".join(archive))

        # Rewrite the active log with only the kept events.
        atomic_write_text(events_path, "".join(keep))

        return RetentionReport(
            archived_count=len(archive),
            remaining_count=len(keep),
            archive_path=str(archive_path),
        )

    def apply_snapshot_retention(
        self,
        policy: RetentionPolicy,
        now: float,
    ) -> RetentionReport:
        """Archive snapshots older than ``now - policy`` days.

        Snapshots whose ``created_at`` is before the cutoff are moved from
        ``snapshots/<name>/`` to ``snapshots/archive/<name>/``. The FOREVER
        policy is a no-op.
        """
        if policy is RetentionPolicy.FOREVER:
            count = self._count_snapshots()
            return RetentionReport(0, count, None)

        cutoff = now - (policy.value * 86400)
        snapshots_dir = self._layout.snapshots_dir
        if not snapshots_dir.exists():
            return RetentionReport(0, 0, None)

        archived = 0
        remaining = 0
        archive_base = self._layout.snapshots_archive_dir
        archive_base.mkdir(parents=True, exist_ok=True)

        for child in sorted(snapshots_dir.iterdir()):
            if not child.is_dir() or child.name == "archive":
                continue
            meta_path = child / "metadata.json"
            if not meta_path.exists():
                remaining += 1
                continue
            try:
                data = json.loads(read_text(meta_path))
                created_at = data.get("created_at", 0)
            except (json.JSONDecodeError, KeyError):
                remaining += 1
                continue

            if created_at < cutoff:
                dest = archive_base / child.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(child), str(dest))
                archived += 1
            else:
                remaining += 1

        return RetentionReport(
            archived_count=archived,
            remaining_count=remaining,
            archive_path=str(archive_base) if archived > 0 else None,
        )

    # ------------------------------------------------------------------ #
    # Internal                                                           #
    # ------------------------------------------------------------------ #

    def _count_events(self) -> int:
        path = self._layout.events_jsonl
        if not path.exists():
            return 0
        count = 0
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    count += 1
        return count

    def _count_snapshots(self) -> int:
        snapshots_dir = self._layout.snapshots_dir
        if not snapshots_dir.exists():
            return 0
        return sum(
            1
            for child in snapshots_dir.iterdir()
            if child.is_dir() and child.name != "archive"
            and (child / "metadata.json").exists()
        )


# --------------------------------------------------------------------------- #
# IntegrityValidator                                                           #
# --------------------------------------------------------------------------- #

class IntegrityValidator:
    """Validates storage integrity across all tiers (docs ``20``, ``62``).

    Checks hash consistency, serialization round-trip integrity, schema version,
    missing references, and corrupted files.
    """

    def __init__(self, layout: StorageLayout) -> None:
        self._layout = layout

    @property
    def layout(self) -> StorageLayout:
        return self._layout

    def validate_graph(self, store: GraphStore) -> IntegrityReport:
        """Validate graph serialization integrity.

        Checks:
        - Round-trip: ``serialize(load(serialize())) == serialize()``
        - Schema version is present and matches.
        - Content hash is computable.
        """
        issues: list[str] = []
        warnings: list[str] = []
        hashes: dict[str, str] = {}

        try:
            text = store.serialize()
            hashes["graph_content"] = sha256_hex(text)

            # Round-trip check.
            reloaded = GraphStore.load(text)
            text2 = reloaded.serialize()
            if text != text2:
                issues.append(
                    "Graph serialization round-trip mismatch: "
                    "serialize(load(x)) != x"
                )

            # Schema version check.
            parsed = json.loads(text)
            sv = parsed.get("schema_version")
            if sv is None:
                warnings.append("Missing schema_version in graph serialization")
            elif sv != SCHEMA_VERSION:
                warnings.append(
                    f"Schema version mismatch: got {sv}, expected {SCHEMA_VERSION}"
                )
        except Exception as exc:
            issues.append(f"Graph validation error: {exc}")

        return IntegrityReport(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            hashes=hashes,
        )

    def validate_events(self, events_path: Path | None = None) -> IntegrityReport:
        """Validate the event log integrity.

        Checks:
        - File exists and is parseable JSONL.
        - Every line is a valid Event dict with an id.
        - No duplicate event ids.
        - Content hash is computable.
        """
        issues: list[str] = []
        warnings: list[str] = []
        hashes: dict[str, str] = {}

        path = events_path or self._layout.events_jsonl
        if not path.exists():
            return IntegrityReport(
                valid=True,
                issues=[],
                warnings=["Event log file does not exist (empty store)"],
                hashes={},
            )

        try:
            content = read_text(path)
            hashes["events_content"] = sha256_hex(content)

            seen_ids: set[str] = set()
            line_num = 0
            for line in content.splitlines():
                line_num += 1
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                except json.JSONDecodeError:
                    issues.append(f"Line {line_num}: invalid JSON")
                    continue

                event_id = data.get("id")
                if event_id is None:
                    issues.append(f"Line {line_num}: missing event id")
                    continue
                if event_id in seen_ids:
                    warnings.append(f"Line {line_num}: duplicate event id {event_id}")
                seen_ids.add(event_id)

                # Validate required fields.
                for field_name in ("event_type", "timestamp", "source"):
                    if field_name not in data:
                        issues.append(
                            f"Line {line_num}: missing required field '{field_name}'"
                        )
        except Exception as exc:
            issues.append(f"Event validation error: {exc}")

        return IntegrityReport(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            hashes=hashes,
        )

    def validate_snapshot(
        self, name: str, snapshots_dir: Path | None = None,
    ) -> IntegrityReport:
        """Validate a named snapshot's integrity.

        Checks:
        - Snapshot directory exists with graph.json and metadata.json.
        - Metadata is valid JSON.
        - Content hash matches metadata.
        - Graph round-trips cleanly.
        - Schema version matches.
        """
        issues: list[str] = []
        warnings: list[str] = []
        hashes: dict[str, str] = {}

        base = snapshots_dir or self._layout.snapshots_dir
        snap_dir = base / name

        if not snap_dir.exists():
            return IntegrityReport(
                valid=False,
                issues=[f"Snapshot directory {snap_dir} does not exist"],
                warnings=[],
                hashes={},
            )

        graph_path = snap_dir / "graph.json"
        meta_path = snap_dir / "metadata.json"

        if not graph_path.exists():
            issues.append(f"Missing graph.json in snapshot {name!r}")
        if not meta_path.exists():
            issues.append(f"Missing metadata.json in snapshot {name!r}")

        if issues:
            return IntegrityReport(valid=False, issues=issues, warnings=warnings, hashes=hashes)

        try:
            graph_text = read_text(graph_path)
            actual_hash = sha256_hex(graph_text)
            hashes["graph_content"] = actual_hash

            meta_data = json.loads(read_text(meta_path))
            expected_hash = meta_data.get("content_hash")
            hashes["metadata_hash"] = expected_hash or ""

            if expected_hash and expected_hash != actual_hash:
                issues.append(
                    f"Hash mismatch in snapshot {name!r}: "
                    f"expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
                )

            # Schema version.
            sv = meta_data.get("schema_version")
            if sv is not None and sv != SCHEMA_VERSION:
                warnings.append(
                    f"Schema version mismatch in snapshot {name!r}: "
                    f"got {sv}, expected {SCHEMA_VERSION}"
                )

            # Round-trip.
            store = GraphStore.load(graph_text)
            text2 = store.serialize()
            if graph_text != text2:
                issues.append(
                    f"Graph round-trip mismatch in snapshot {name!r}"
                )
        except Exception as exc:
            issues.append(f"Snapshot validation error for {name!r}: {exc}")

        return IntegrityReport(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            hashes=hashes,
        )

    def validate_checkpoint(
        self,
        graph_store: PersistentGraphStore,
        name: str = "latest",
    ) -> IntegrityReport:
        """Validate a named checkpoint's integrity.

        Checks:
        - Checkpoint file exists.
        - Content is valid JSON.
        - Graph round-trips cleanly.
        - Content hash is computable.
        """
        issues: list[str] = []
        warnings: list[str] = []
        hashes: dict[str, str] = {}

        path = graph_store._layout.checkpoints_dir / f"{name}.json"
        if not path.exists():
            return IntegrityReport(
                valid=False,
                issues=[f"Checkpoint {name!r} does not exist at {path}"],
                warnings=[],
                hashes={},
            )

        try:
            text = read_text(path)
            hashes["checkpoint_content"] = sha256_hex(text)

            # Round-trip.
            store = GraphStore.load(text)
            text2 = store.serialize()
            if text != text2:
                issues.append(
                    f"Checkpoint round-trip mismatch for {name!r}"
                )

            # Schema version.
            parsed = json.loads(text)
            sv = parsed.get("schema_version")
            if sv is not None and sv != SCHEMA_VERSION:
                warnings.append(
                    f"Schema version mismatch in checkpoint {name!r}: "
                    f"got {sv}, expected {SCHEMA_VERSION}"
                )
        except Exception as exc:
            issues.append(f"Checkpoint validation error for {name!r}: {exc}")

        return IntegrityReport(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            hashes=hashes,
        )
