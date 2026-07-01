#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hash-chain audit logger for trusted RAG security events."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from . import paths
from .hash_chain import append_hash_chain_record


class AuditLogger:
    def __init__(self, audit_dir: str | Path | None = None) -> None:
        paths.ensure_runtime_dirs()
        self.audit_dir = Path(audit_dir) if audit_dir else paths.AUDIT_DIR
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def log_path_for_today(self) -> Path:
        return self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = append_hash_chain_record(self.log_path_for_today(), event_type, payload)
        return {
            **record,
            "audit_id": record["record_hash"],
            "audit_path": str(self.log_path_for_today()),
        }
