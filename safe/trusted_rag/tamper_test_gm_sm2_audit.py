#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tamper test for SM3+SM2 multimodal audit logs."""

from __future__ import annotations

import json
from pathlib import Path

from .multimodal_gm_sm2_audit_logger import append_gm_sm2_audit, latest_audit_path, verify_gm_sm2_audit


def _ensure_audit() -> Path:
    path = latest_audit_path()
    if not path.exists():
        append_gm_sm2_audit(
            {
                "query": "demo",
                "visual_guard_risk_level": "low",
                "visual_guard_results": [{"page": 1, "hash": "demo", "text_hash": "demo"}],
            }
        )
    return latest_audit_path()


def _tamper(path: Path) -> Path:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    if not records:
        raise RuntimeError("no audit records to tamper")
    payload = records[-1].setdefault("payload", {})
    payload["query"] = str(payload.get("query", "")) + " TAMPERED"
    payload["visual_guard_risk_level"] = "keep"
    if payload.get("visual_guard_results"):
        payload["visual_guard_results"][0]["page"] = 999999
        payload["visual_guard_results"][0]["hash"] = "tampered_visual_hash"
        payload["visual_guard_results"][0]["text_hash"] = "tampered_text_hash"
    tampered = path.with_name("TAMPERED_" + path.name)
    with tampered.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return tampered


def main() -> int:
    original = _ensure_audit()
    original_result = verify_gm_sm2_audit(original)
    tampered = _tamper(original)
    tampered_result = verify_gm_sm2_audit(tampered)
    tamper_detected = not tampered_result["ok"]
    ok = original_result["ok"] and tamper_detected
    print(f"original_ok = {original_result['ok']}")
    print(f"tamper_detected = {tamper_detected}")
    print(f"result = {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
