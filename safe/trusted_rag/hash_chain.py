#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic hash-chain JSONL audit utilities."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_json(obj: Any) -> str:
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_text(data)


def _last_record_hash(jsonl_path: Path) -> str:
    if not jsonl_path.exists():
        return ""

    last_line = ""
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                last_line = stripped

    if not last_line:
        return ""
    try:
        return str(json.loads(last_line).get("record_hash", ""))
    except json.JSONDecodeError:
        return ""


def append_hash_chain_record(
    jsonl_path: str | Path, event_type: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    path = Path(jsonl_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = _last_record_hash(path)
    record_without_hash = {
        "timestamp": _utc_now(),
        "event_type": event_type,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    record = {**record_without_hash, "record_hash": hash_json(record_without_hash)}
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def verify_hash_chain(jsonl_path: str | Path) -> Dict[str, Any]:
    path = Path(jsonl_path)
    result = {
        "ok": True,
        "path": str(path),
        "exists": path.exists(),
        "count": 0,
        "last_hash": "",
        "errors": [],
    }
    if not path.exists():
        result["ok"] = False
        result["errors"].append("audit log does not exist")
        return result

    prev_hash = ""
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            result["count"] += 1
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                result["ok"] = False
                result["errors"].append(f"line {line_no}: invalid JSON: {exc}")
                continue

            for key in ("timestamp", "event_type", "payload", "prev_hash", "record_hash"):
                if key not in record:
                    result["ok"] = False
                    result["errors"].append(f"line {line_no}: missing {key}")

            if record.get("prev_hash") != prev_hash:
                result["ok"] = False
                result["errors"].append(
                    f"line {line_no}: prev_hash mismatch, expected {prev_hash!r}"
                )

            record_hash = record.get("record_hash", "")
            recomputed = hash_json({k: v for k, v in record.items() if k != "record_hash"})
            if record_hash != recomputed:
                result["ok"] = False
                result["errors"].append(f"line {line_no}: record_hash mismatch")

            prev_hash = str(record_hash)

    result["last_hash"] = prev_hash
    return result
