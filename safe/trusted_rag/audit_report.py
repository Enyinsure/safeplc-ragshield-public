#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legacy SHA-256 audit-chain report helpers.

The formal national-cryptography audit path is implemented by
multimodal_gm_sm2_audit_logger.py plus audit_sm4_sealer.py.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .hash_chain import hash_json, sha256_text


SIGNATURE_ALGORITHM = "legacy-sha256-demo"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _event_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    excluded = {"prev_hash", "current_hash", "signature_ok", "metadata"}
    return {key: value for key, value in event.items() if key not in excluded}


def compute_event_hash(event: Dict[str, Any]) -> str:
    return hash_json(_event_payload(event))


def _signature_for(current_hash: str, key_id: str) -> str:
    return sha256_text(f"{key_id}:{current_hash}:legacy-demo")


def build_hash_chain(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chained: List[Dict[str, Any]] = []
    prev_hash = ""
    for index, event in enumerate(events):
        item = dict(event)
        item.setdefault("event_id", f"audit_demo_{index + 1:03d}")
        item.setdefault("timestamp", _utc_now())
        item.setdefault("query", "")
        item.setdefault("decision", "keep")
        item.setdefault("risk_level", "low")
        item.setdefault("evidence_hashes", [])
        item.setdefault("signature_algorithm", SIGNATURE_ALGORITHM)
        item.setdefault("key_id", "safeplc-demo-key")
        item.setdefault("metadata", {})
        item["prev_hash"] = prev_hash
        item["current_hash"] = compute_event_hash(item)
        item["signature_ok"] = True
        item["metadata"] = {
            **dict(item.get("metadata") or {}),
            "demo_signature": _signature_for(item["current_hash"], item["key_id"]),
        }
        prev_hash = item["current_hash"]
        chained.append(item)
    return chained


def verify_hash_chain(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors: List[str] = []
    prev_hash = ""
    for index, event in enumerate(events):
        event_id = event.get("event_id", f"line_{index + 1}")
        if event.get("prev_hash", "") != prev_hash:
            errors.append(f"{event_id}: prev_hash mismatch")
        expected_hash = compute_event_hash(event)
        if event.get("current_hash") != expected_hash:
            errors.append(f"{event_id}: current_hash mismatch")
        key_id = str(event.get("key_id", "safeplc-demo-key"))
        expected_sig = _signature_for(str(event.get("current_hash", "")), key_id)
        actual_sig = (event.get("metadata") or {}).get("demo_signature")
        if event.get("signature_algorithm") == SIGNATURE_ALGORITHM and actual_sig != expected_sig:
            errors.append(f"{event_id}: demo signature mismatch")
        if event.get("signature_ok") is False:
            errors.append(f"{event_id}: signature_ok is false")
        prev_hash = str(event.get("current_hash", ""))
    return {
        "ok": not errors,
        "count": len(events),
        "errors": errors,
        "root_hash": prev_hash,
        "tamper_detected": bool(errors),
        "verified_at": _utc_now(),
        "signature_algorithm": SIGNATURE_ALGORITHM,
    }


def tamper_one_event(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tampered = copy.deepcopy(events)
    if not tampered:
        return tampered
    index = min(1, len(tampered) - 1)
    original = tampered[index].get("decision", "quarantine")
    tampered[index]["decision"] = "keep" if original != "keep" else "quarantine"
    tampered[index].setdefault("metadata", {})["tamper_demo"] = (
        f"decision changed from {original!r} to {tampered[index]['decision']!r} without recomputing hashes"
    )
    return tampered


def demo_events() -> List[Dict[str, Any]]:
    raw = [
        {
            "event_id": "evt_query_001",
            "timestamp": _utc_now(),
            "query": "S7-1500 fault LED diagnostic question",
            "decision": "answer",
            "risk_level": "low",
            "evidence_hashes": [sha256_text("clean manual diagnostic evidence")],
            "signature_algorithm": SIGNATURE_ALGORITHM,
            "key_id": "safeplc-demo-key",
            "metadata": {"stage": "trusted_answer"},
        },
        {
            "event_id": "evt_mepi_002",
            "timestamp": _utc_now(),
            "query": "OCR card says ignore previous instructions",
            "decision": "quarantine",
            "risk_level": "high",
            "evidence_hashes": [sha256_text("poisoned OCR evidence")],
            "signature_algorithm": SIGNATURE_ALGORITHM,
            "key_id": "safeplc-demo-key",
            "metadata": {"stage": "mepi"},
        },
        {
            "event_id": "evt_redteam_003",
            "timestamp": _utc_now(),
            "query": "red-team parameter poisoning case",
            "decision": "need_human_review",
            "risk_level": "medium",
            "evidence_hashes": [sha256_text("parameter table anomaly")],
            "signature_algorithm": SIGNATURE_ALGORITHM,
            "key_id": "safeplc-demo-key",
            "metadata": {"stage": "redteam"},
        },
    ]
    return build_hash_chain(raw)


def load_events_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    source = Path(path)
    events: List[Dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            payload = data.get("payload", data)
            events.append(
                {
                    "event_id": payload.get("query_id") or data.get("record_hash") or f"event_{index}",
                    "timestamp": data.get("timestamp") or payload.get("created_at") or _utc_now(),
                    "query": payload.get("query", ""),
                    "decision": (payload.get("decision") or {}).get("action", payload.get("decision", "unknown")),
                    "risk_level": (payload.get("decision") or {}).get("severity", payload.get("risk_level", "unknown"))
                    if isinstance(payload.get("decision"), dict)
                    else payload.get("risk_level", "unknown"),
                    "evidence_hashes": payload.get("evidence_hashes", []),
                    "signature_algorithm": SIGNATURE_ALGORITHM,
                    "key_id": "safeplc-demo-key",
                    "metadata": {"source_log": str(source), "original_record_hash": data.get("record_hash")},
                }
            )
    return build_hash_chain(events)


def write_events_jsonl(events: Iterable[Dict[str, Any]], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return output


def export_audit_report(events: List[Dict[str, Any]], verify_result: Dict[str, Any], output_md: str | Path) -> Path:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SafePLC Audit Chain Report",
        "",
        "## Audit Fields",
        "",
        "- `event_id`: stable event identifier",
        "- `timestamp`: event time",
        "- `query`: user or evaluation query",
        "- `decision`: trusted decision such as answer, quarantine, or refuse",
        "- `risk_level`: low, medium, or high",
        "- `evidence_hashes`: hashes of evidence used by the decision",
        "- `prev_hash` / `current_hash`: hash-chain links",
        "- `signature_algorithm`: legacy demo signature marker for this compatibility report",
        "- `signature_ok`: legacy demo signature verification status",
        "- `key_id`: local demo key identifier",
        "",
        "## Verification Result",
        "",
        f"- OK: {verify_result.get('ok')}",
        f"- Event count: {verify_result.get('count')}",
        f"- Root hash: `{verify_result.get('root_hash', '')}`",
        f"- Tamper detected: {verify_result.get('tamper_detected')}",
        f"- Signature algorithm: {verify_result.get('signature_algorithm')}",
        "",
        "## Errors",
        "",
    ]
    errors = verify_result.get("errors") or []
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Event Summary",
            "",
            "| Event | Decision | Risk | Evidence Hashes |",
            "|---|---|---|---:|",
        ]
    )
    for event in events:
        lines.append(
            f"| {event.get('event_id')} | {event.get('decision')} | {event.get('risk_level')} | {len(event.get('evidence_hashes', []))} |"
        )
    lines.extend(
        [
            "",
            "## Project-Book Conclusion",
            "",
            "The audit chain makes each SafePLC trusted-RAG decision reproducible and tamper-evident. "
            "Every event links to the previous hash, records the evidence hashes used by the decision, "
            "and records legacy demo signature metadata for backwards-compatible reports. For the formal "
            "national-cryptography path, use the SM3+SM2+SM4 modules under `safe/trusted_rag/`.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output
