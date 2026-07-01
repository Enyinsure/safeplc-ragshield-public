#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Field-level tamper matrix for GM audit records."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List

from . import paths
from .multimodal_gm_sm2_audit_logger import append_gm_sm2_audit, latest_audit_path, verify_gm_sm2_audit


Mutation = Callable[[Dict[str, Any]], None]


def _ensure_matrix_audit() -> Path:
    append_gm_sm2_audit(
        {
            "query": "terminal wiring power module",
            "action": "clarify",
            "answer": "Please provide the exact PLC model or order number before wiring guidance.",
            "risk_flags": ["missing_model_or_order"],
            "visual_guard_results": [
                {
                    "evidence_id": "pdf_page_01965",
                    "decision": "keep_as_risk_evidence",
                    "page": 1965,
                    "hash": "visual_hash_demo",
                    "text_hash": "visual_text_hash_demo",
                }
            ],
        }
    )
    return latest_audit_path()


def _records(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _write_records(path: Path, records: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _payload(record: Dict[str, Any]) -> Dict[str, Any]:
    payload = record.setdefault("payload", {})
    if not isinstance(payload, dict):
        record["payload"] = {}
    return record["payload"]


def _first_visual(record: Dict[str, Any]) -> Dict[str, Any]:
    payload = _payload(record)
    results = payload.setdefault("visual_guard_results", [{}])
    if not results:
        results.append({})
    return results[0]


def _run_one(source: Path, name: str, mutate: Mutation) -> bool:
    records = _records(source)
    if not records:
        raise RuntimeError("no audit records to tamper")
    tampered_records = deepcopy(records)
    mutate(tampered_records[-1])
    target = source.with_name(f"MATRIX_TAMPER_{name}_{source.name}")
    _write_records(target, tampered_records)
    return not verify_gm_sm2_audit(target)["ok"]


def run_matrix() -> Dict[str, Any]:
    source = _ensure_matrix_audit()
    mutations: Dict[str, Mutation] = {
        "query": lambda record: _payload(record).__setitem__("query", "tampered query"),
        "answer": lambda record: _payload(record).__setitem__("answer", "tampered answer"),
        "action": lambda record: _payload(record).__setitem__("action", "answer"),
        "visual_page": lambda record: _first_visual(record).__setitem__("page", 999999),
        "visual_hash": lambda record: _first_visual(record).__setitem__("hash", "tampered_visual_hash"),
        "visual_text_hash": lambda record: _first_visual(record).__setitem__("text_hash", "tampered_text_hash"),
        "mepi_decision": lambda record: _first_visual(record).__setitem__("decision", "quarantine"),
        "risk_flags": lambda record: _payload(record).__setitem__("risk_flags", ["tampered_flag"]),
        "prev_hash": lambda record: record.__setitem__("prev_hash", "tampered_prev_hash"),
        "record_hash": lambda record: record.__setitem__("record_hash", "0" * 64),
        "signature": lambda record: record.__setitem__("sm2_signature", "0" * 128),
    }
    results = {name: _run_one(source, name, mutate) for name, mutate in mutations.items()}
    summary = {f"tamper_{name}": "detected" if detected else "missed" for name, detected in results.items()}
    summary["matrix_pass"] = all(results.values())
    summary["source_audit_path"] = str(source)
    return summary


def write_matrix_report(summary: Dict[str, Any]) -> tuple[Path, Path]:
    paths.FINAL_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_md = paths.FINAL_REPORT_DIR / f"GM_AUDIT_TAMPER_MATRIX_{stamp}.md"
    out_json = paths.FINAL_REPORT_DIR / f"GM_AUDIT_TAMPER_MATRIX_{stamp}.json"
    lines = ["# GM Audit Tamper Matrix", ""]
    lines.extend(f"- {key} = {value}" for key, value in summary.items())
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_md, out_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no_write", action="store_true")
    args = parser.parse_args()
    summary = run_matrix()
    if not args.no_write:
        out_md, out_json = write_matrix_report(summary)
        summary["out_md"] = str(out_md)
        summary["out_json"] = str(out_json)
    for key in [
        "tamper_query",
        "tamper_answer",
        "tamper_action",
        "tamper_visual_page",
        "tamper_visual_hash",
        "tamper_visual_text_hash",
        "tamper_mepi_decision",
        "tamper_risk_flags",
        "tamper_prev_hash",
        "tamper_record_hash",
        "tamper_signature",
        "matrix_pass",
    ]:
        print(f"{key} = {summary[key]}")
    return 0 if summary["matrix_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

