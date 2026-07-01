#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SM3-only compatibility audit logger for multimodal events."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from . import paths
from .gm_crypto import canonical_json_hash


def append_multimodal_gm_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    paths.AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    path = paths.AUDIT_DIR / f"audit_multimodal_gm_{datetime.now().strftime('%Y%m%d')}.jsonl"
    prev_hash = ""
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                prev_hash = json.loads(line).get("record_hash", "")
    record = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "trusted_multimodal_query_gm",
        "hash_algorithm": "SM3",
        "payload": payload,
        "prev_hash": prev_hash,
    }
    record["record_hash"] = canonical_json_hash(record)
    record["audit_id"] = record["record_hash"]
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    record["audit_path"] = str(path)
    return record


if __name__ == "__main__":
    result = append_multimodal_gm_audit({"query": "demo"})
    print("hash_algorithm = SM3")
    print(f"audit_id = {result['audit_id']}")
