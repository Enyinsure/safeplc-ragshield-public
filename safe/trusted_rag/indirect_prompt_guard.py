#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan retrieved evidence for indirect prompt injection."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .evidence_schema import EvidenceRecord
from .poison_scanner import SEVERITY_ORDER, scan_text


def _record_text(record: EvidenceRecord | Dict[str, Any]) -> str:
    if isinstance(record, EvidenceRecord):
        return record.text
    return str(record.get("text", ""))


def _record_id(record: EvidenceRecord | Dict[str, Any]) -> str:
    if isinstance(record, EvidenceRecord):
        return record.source_id or record.chunk_id
    return str(record.get("source_id") or record.get("chunk_id") or record.get("id") or "")


def scan_evidence_record(record: EvidenceRecord | Dict[str, Any]) -> Dict[str, Any]:
    result = scan_text(_record_text(record))
    flags = list(result["risk_flags"])
    if flags:
        flags.append("indirect_prompt_injection")
    return {
        "source_id": _record_id(record),
        "risk_flags": sorted(set(flags)),
        "severity": result["severity"],
        "reason": result["reason"],
        "matched_patterns": result["matched_patterns"],
    }


def scan_evidence_records(records: Iterable[EvidenceRecord | Dict[str, Any]]) -> Dict[str, Any]:
    per_record = [scan_evidence_record(record) for record in records]
    all_flags = sorted({flag for item in per_record for flag in item["risk_flags"]})
    severity = max(
        (item["severity"] for item in per_record),
        key=lambda item: SEVERITY_ORDER.get(item, 0),
        default="low",
    )
    risky = [item for item in per_record if item["risk_flags"]]
    return {
        "risk_flags": all_flags,
        "severity": severity,
        "reason": "Indirect prompt risk detected in evidence." if risky else "No evidence poison pattern matched.",
        "records": per_record,
    }
