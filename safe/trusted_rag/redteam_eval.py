#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run red-team cases against the trusted RAG pipeline."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from . import paths
from .audit_logger import AuditLogger
from .trusted_query import trusted_answer


CASES_PATH = paths.TESTS_DIR / "redteam_cases.jsonl"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_cases(path: Path = CASES_PATH) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                cases.append(json.loads(stripped))
    return cases


def run_eval() -> Dict[str, Any]:
    paths.ensure_runtime_dirs()
    cases = load_cases()
    results = []
    for case in cases:
        answer = trusted_answer(case["query"])
        actual = answer.action
        expected = case["expected_action"]
        results.append(
            {
                "id": case["id"],
                "category": case["category"],
                "query": case["query"],
                "expected_action": expected,
                "actual_action": actual,
                "passed": actual == expected,
                "risk_flags": answer.risk_flags,
                "evidence_count": len(answer.evidence),
                "audit_id": answer.audit_id,
            }
        )
    passed = sum(1 for item in results if item["passed"])
    return {
        "generated_at": datetime.now().isoformat(),
        "case_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def write_reports(report: Dict[str, Any]) -> Dict[str, str]:
    paths.EVAL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    json_path = paths.EVAL_DIR / f"redteam_eval_{stamp}.json"
    md_path = paths.EVAL_DIR / f"redteam_eval_summary_{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# SafePLC Trusted RAG Red-Team Eval",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Cases: {report['case_count']}",
        f"- Passed: {report['passed']}",
        f"- Failed: {report['failed']}",
        "",
        "| ID | Category | Expected | Actual | Pass |",
        "|---|---|---:|---:|---:|",
    ]
    for item in report["results"]:
        mark = "yes" if item["passed"] else "no"
        lines.append(
            f"| {item['id']} | {item['category']} | {item['expected_action']} | {item['actual_action']} | {mark} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def main() -> int:
    report = run_eval()
    outputs = write_reports(report)
    AuditLogger().log_event("redteam_eval_completed", {"summary": report, "outputs": outputs})
    print(json.dumps({"outputs": outputs, **report}, ensure_ascii=False, indent=2))
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
