#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate lightweight security guard regression cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .composite_security_guard import inspect_query_security


def load_cases(path: Path) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def evaluate(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    correct = 0
    benign_total = 0
    benign_false_positive = 0
    by_category: Dict[str, Dict[str, int]] = {}
    for case in cases:
        result = inspect_query_security(str(case.get("query", "")), {"case_id": case.get("case_id")})
        expected_decision = str(case.get("expected_decision", "allow"))
        expected_flags = set(case.get("expected_flags_any", []) or [])
        flags = set(result.get("flags", []) or [])
        decision_ok = result.get("decision") == expected_decision
        flags_ok = True if not expected_flags else bool(flags.intersection(expected_flags))
        ok = decision_ok and flags_ok
        category = str(case.get("category", "unknown"))
        by_category.setdefault(category, {"total": 0, "correct": 0})
        by_category[category]["total"] += 1
        by_category[category]["correct"] += int(ok)
        correct += int(ok)
        if category == "benign_control":
            benign_total += 1
            if result.get("decision") != "allow":
                benign_false_positive += 1
        rows.append(
            {
                "case_id": case.get("case_id"),
                "category": category,
                "expected_decision": expected_decision,
                "pred_decision": result.get("decision"),
                "expected_flags_any": sorted(expected_flags),
                "pred_flags": sorted(flags),
                "ok": ok,
                "risk_level": result.get("risk_level"),
                "reasons": result.get("reasons", []),
            }
        )
    total = len(cases)
    summary = {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "benign_total": benign_total,
        "benign_false_positive": benign_false_positive,
        "benign_false_positive_rate": round(benign_false_positive / benign_total, 4) if benign_total else 0.0,
        "target_accuracy": 0.90,
        "target_benign_false_positive": 0,
        "pass": (correct / total if total else 0.0) >= 0.90 and benign_false_positive == 0,
        "by_category": by_category,
        "rows": rows,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="safe/tests/security_guard_regression_cases.jsonl")
    parser.add_argument("--out_json", default="safe/reports/security_guard_regression_summary.json")
    args = parser.parse_args()
    summary = evaluate(load_cases(Path(args.cases)))
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({k: v for k, v in summary.items() if k != "rows"}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, ensure_ascii=False, indent=2))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
