#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibility wrapper for multimodal audit logging."""

from __future__ import annotations

from typing import Any, Dict

from .audit_logger import AuditLogger


def append_multimodal_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    return AuditLogger().log_event("trusted_multimodal_query", payload)


if __name__ == "__main__":
    record = append_multimodal_audit({"query": "demo", "decision": "answer"})
    print(f"audit_id = {record['audit_id']}")
    print(f"audit_path = {record['audit_path']}")
