#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export a self-contained evidence bundle from an audit record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from . import paths
from .multimodal_gm_sm2_audit_logger import (
    SIGNER_ID,
    _read_records,
    append_gm_sm2_audit,
    latest_audit_path,
    public_key_fingerprint,
    record_body_for_hash,
)


def _audit_records() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in sorted(paths.AUDIT_DIR.glob("audit_multimodal_gm_sm2_*.jsonl")):
        records.extend(_read_records(path))
    return records


def _ensure_latest_record() -> Dict[str, Any]:
    records = _read_records(latest_audit_path())
    if records:
        return records[-1]
    return append_gm_sm2_audit(
        {
            "query": "bundle export demo",
            "action": "answer",
            "answer": "demo",
            "risk_flags": [],
            "visual_guard_results": [],
        }
    )


def _record_by_audit_id(audit_id: str | None) -> Dict[str, Any]:
    if not audit_id:
        return _ensure_latest_record()
    for record in _audit_records():
        if str(record.get("audit_id", "")) == audit_id:
            return record
    raise SystemExit(f"audit_id not found: {audit_id}")


def _hashes(items: Iterable[Dict[str, Any]]) -> List[str]:
    hashes = []
    for item in items or []:
        value = item.get("hash") or item.get("evidence_hash") or item.get("text_hash")
        if value:
            hashes.append(str(value))
    return hashes


def _visual_hashes(payload: Dict[str, Any]) -> List[str]:
    fields = ["kept_visual_evidence", "quarantined_visual_evidence", "risk_visual_evidence", "visual_guard_results"]
    hashes: List[str] = []
    for field in fields:
        values = payload.get(field) or []
        if isinstance(values, list):
            hashes.extend(_hashes(item for item in values if isinstance(item, dict)))
    return sorted(set(hashes))


def _text_hashes(payload: Dict[str, Any]) -> List[str]:
    values = payload.get("text_evidence_hashes") or payload.get("text_evidence") or []
    if isinstance(values, list):
        return sorted(set(_hashes(item for item in values if isinstance(item, dict))))
    return []


def build_bundle(record: Dict[str, Any]) -> Dict[str, Any]:
    payload = record.get("payload", {}) if isinstance(record.get("payload", {}), dict) else {}
    public_key = str(record.get("sm2_public_key", ""))
    return {
        "bundle_version": "1.0",
        "audit_id": str(record.get("audit_id", "")),
        "signer_id": str(record.get("signer_id", SIGNER_ID)),
        "hash_algorithm": str(record.get("hash_algorithm", "SM3")),
        "signature_algorithm": str(record.get("signature_algorithm", "SM2")),
        "public_key_fingerprint": str(record.get("public_key_fingerprint", public_key_fingerprint(public_key))),
        "query": payload.get("query", ""),
        "action": payload.get("action", ""),
        "answer": payload.get("answer", ""),
        "risk_flags": payload.get("risk_flags", []),
        "text_evidence_hashes": _text_hashes(payload),
        "visual_evidence_hashes": _visual_hashes(payload),
        "mepi_decisions": [
            item.get("decision", "")
            for item in payload.get("visual_guard_results", [])
            if isinstance(item, dict) and item.get("decision")
        ],
        "prev_hash": str(record.get("prev_hash", "")),
        "record_hash": str(record.get("record_hash", "")),
        "sm2_public_key": public_key,
        "sm2_signature": str(record.get("sm2_signature", "")),
        "record_body": record_body_for_hash(record),
    }


def export_bundle(audit_id: str | None = None, out_dir: str | Path | None = None) -> Path:
    record = _record_by_audit_id(audit_id)
    bundle = build_bundle(record)
    directory = Path(out_dir) if out_dir else paths.SAFE_DIR / "reports" / "audit_bundles"
    directory.mkdir(parents=True, exist_ok=True)
    safe_audit_id = bundle["audit_id"][:32] or "unknown"
    output = directory / f"bundle_{safe_audit_id}.json"
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--latest", action="store_true")
    group.add_argument("--audit_id")
    parser.add_argument("--out_dir")
    args = parser.parse_args()
    output = export_bundle(args.audit_id, args.out_dir)
    print(f"bundle_path = {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

