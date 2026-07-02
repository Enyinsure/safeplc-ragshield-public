#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SM3+SM2 audit logger for trusted multimodal queries."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from . import paths
from .audit_sm4_sealer import seal_audit_log
from .gm_crypto import canonical_json_hash, sm3_hash_text
from .gm_sm2 import load_or_create_keys, sign_digest, verify_digest


EVENT_TYPE = "trusted_multimodal_query_gm_sm2"
SIGNER_ID = "SafePLC-RAGShield-local-audit-node"


def _now() -> str:
    return datetime.now().isoformat()


def _audit_dir(audit_dir: str | Path | None = None) -> Path:
    directory = Path(audit_dir) if audit_dir else paths.AUDIT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def latest_audit_path(audit_dir: str | Path | None = None) -> Path:
    directory = _audit_dir(audit_dir)
    existing = sorted(directory.glob("audit_multimodal_gm_sm2_*.jsonl"))
    if existing:
        return existing[-1]
    return directory / f"audit_multimodal_gm_sm2_{datetime.now().strftime('%Y%m%d')}.jsonl"


def _last_hash(path: Path) -> str:
    if not path.exists():
        return ""
    last = ""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line.strip()
    if not last:
        return ""
    try:
        return str(json.loads(last).get("record_hash", ""))
    except Exception:
        return ""


def public_key_fingerprint(public_key_hex: str) -> str:
    return sm3_hash_text(public_key_hex)


def record_body_for_hash(record: Dict[str, Any]) -> Dict[str, Any]:
    body = {
        "timestamp": record["timestamp"],
        "event_type": record["event_type"],
        "hash_algorithm": record["hash_algorithm"],
        "signature_algorithm": record["signature_algorithm"],
        "payload": record["payload"],
        "prev_hash": record["prev_hash"],
    }
    if "signer_id" in record:
        body["signer_id"] = record.get("signer_id", "")
    if "public_key_fingerprint" in record:
        body["public_key_fingerprint"] = record.get("public_key_fingerprint", "")
    return body


def append_gm_sm2_audit(payload: Dict[str, Any], audit_dir: str | Path | None = None) -> Dict[str, Any]:
    path = _audit_dir(audit_dir) / f"audit_multimodal_gm_sm2_{datetime.now().strftime('%Y%m%d')}.jsonl"
    private, public = load_or_create_keys()
    record = {
        "timestamp": _now(),
        "event_type": EVENT_TYPE,
        "signer_id": SIGNER_ID,
        "hash_algorithm": "SM3",
        "signature_algorithm": "SM2",
        "public_key_fingerprint": public_key_fingerprint(public),
        "payload": payload,
        "prev_hash": _last_hash(path),
    }
    record["record_hash"] = canonical_json_hash(record_body_for_hash(record))
    record["audit_id"] = record["record_hash"]
    record["sm2_public_key"] = public
    record["sm2_signature"] = sign_digest(record["record_hash"], private)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    record["audit_path"] = str(path)
    try:
        seal_result = seal_audit_log(path)
        record["sm4_encryption_algorithm"] = seal_result["algorithm"]
        record["sm4_sealed_path"] = seal_result["sealed_path"]
        record["sm4_seal_ok"] = True
    except Exception as exc:
        record["sm4_seal_ok"] = False
        record["sm4_seal_error"] = str(exc)
    return record


def _read_records(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def verify_gm_sm2_audit(path: str | Path | None = None) -> Dict[str, Any]:
    audit_path = Path(path) if path else latest_audit_path()
    records = _read_records(audit_path)
    errors = []
    fingerprint_errors = []
    prev_hash = ""
    for index, record in enumerate(records, start=1):
        expected_hash = canonical_json_hash(record_body_for_hash(record))
        if record.get("prev_hash") != prev_hash:
            errors.append(f"line {index}: prev_hash mismatch")
        if record.get("record_hash") != expected_hash:
            errors.append(f"line {index}: record_hash mismatch")
        fingerprint = record.get("public_key_fingerprint")
        if fingerprint and fingerprint != public_key_fingerprint(str(record.get("sm2_public_key", ""))):
            fingerprint_errors.append(f"line {index}: public key fingerprint mismatch")
        if not verify_digest(
            str(record.get("record_hash", "")),
            str(record.get("sm2_signature", "")),
            str(record.get("sm2_public_key", "")),
        ):
            errors.append(f"line {index}: sm2 signature mismatch")
        prev_hash = str(record.get("record_hash", ""))
    errors.extend(fingerprint_errors)
    return {
        "path": str(audit_path),
        "count": len(records),
        "hash_chain_ok": not any("prev_hash" in error or "record_hash" in error for error in errors),
        "sm2_signature_ok": not any("signature" in error for error in errors),
        "public_key_fingerprint_ok": not fingerprint_errors,
        "ok": not errors,
        "errors": errors,
    }


def main() -> int:
    path = latest_audit_path()
    if not path.exists():
        append_gm_sm2_audit({"query": "demo", "visual_guard_risk_level": "low"})
    result = verify_gm_sm2_audit(path)
    print("hash_algorithm = SM3")
    print("signature_algorithm = SM2")
    print("encryption_algorithm = SM4-CBC-PKCS7")
    print(f"hash_chain_ok = {result['hash_chain_ok']}")
    print(f"sm2_signature_ok = {result['sm2_signature_ok']}")
    print(f"public_key_fingerprint_ok = {result['public_key_fingerprint_ok']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
