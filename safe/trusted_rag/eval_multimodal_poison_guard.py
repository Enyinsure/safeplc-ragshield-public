#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate the M-EPI visual evidence guard on JSONL cases."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from .multimodal_poison_guard import inspect_visual_evidence


def load_cases(path: Path) -> List[Dict[str, Any]]:
    cases = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                cases.append(json.loads(stripped))
    return cases


def evaluate(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    by_category: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0})
    confusion = Counter()
    for case in cases:
        result = inspect_visual_evidence(case.get("evidence", {}))
        expected = case.get("expected_decision")
        pred = result["decision"]
        ok = pred == expected
        category = case.get("category", "unknown")
        by_category[category]["total"] += 1
        by_category[category]["correct"] += int(ok)
        confusion[f"{expected}->{pred}"] += 1
        rows.append(
            {
                "case_id": case.get("case_id", ""),
                "category": category,
                "expected_decision": expected,
                "pred_decision": pred,
                "ok": ok,
                "risk_level": result["risk_level"],
                "flags": ";".join(result["flags"]),
                "reasons": "; ".join(result["reasons"]),
            }
        )
    total = len(rows)
    correct = sum(1 for row in rows if row["ok"])
    return {
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "by_category": dict(by_category),
        "confusion": dict(confusion),
        "rows": rows,
    }


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "case_id",
        "category",
        "expected_decision",
        "pred_decision",
        "ok",
        "risk_level",
        "flags",
        "reasons",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--out_csv", required=True)
    parser.add_argument("--summary_json", required=True)
    args = parser.parse_args(argv)

    cases = load_cases(Path(args.cases))
    result = evaluate(cases)
    out_csv = Path(args.out_csv)
    summary_json = Path(args.summary_json)
    write_csv(result["rows"], out_csv)
    summary = {key: value for key, value in result.items() if key != "rows"}
    summary["out_csv"] = str(out_csv)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result["accuracy"] == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
