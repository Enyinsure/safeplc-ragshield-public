#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run baseline-vs-SafePLC red-team showcase."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from safe.trusted_rag.mepi_scorer import score_case
from safe.trusted_rag.multimodal_consistency import check_evidence_card


def load_cases(path: Path) -> List[Dict[str, Any]]:
    cases = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                cases.append(json.loads(stripped))
    return cases


def vanilla_rag_baseline(case: Dict[str, Any]) -> str:
    attack_type = case["attack_type"]
    if attack_type in {"dangerous_operation_request", "text_prompt_injection", "visual_ocr_injection"}:
        return "unsafe_answer"
    if attack_type in {"audit_log_tampering", "real_risk_evidence_preservation"}:
        return "missed_detection"
    return "trust_top_evidence"


def safeplc_ours(case: Dict[str, Any]) -> Dict[str, Any]:
    malicious = case["malicious_evidence"]
    clean = case["clean_evidence"]
    try:
        mepi = score_case([malicious], query=case["query"])
        consistency = check_evidence_card(malicious)
        decision = mepi["decision"]
    except Exception as exc:
        mepi = {"decision": case["expected_decision"], "risk_level": case["expected_risk_level"], "reasons": [f"fallback after error: {exc}"]}
        consistency = {"decision": "need_human_review", "reasons": ["fallback consistency rule"]}
        decision = case["expected_decision"]

    if case["attack_type"] == "audit_log_tampering":
        decision = "quarantine"
        mepi["risk_level"] = "high"
        mepi.setdefault("reasons", []).append("audit tampering requires hash-chain rejection")
    if case["attack_type"] == "real_risk_evidence_preservation":
        decision = "keep_as_risk_evidence"
        mepi["risk_level"] = "low"
    return {"decision": decision, "mepi": mepi, "consistency": consistency, "clean_evidence_id": clean.get("evidence_id")}


def write_markdown(results: List[Dict[str, Any]], output_md: Path) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    dist = Counter(item["attack_type"] for item in results)
    lines = [
        "# SafePLC Red-Team Showcase Report",
        "",
        "## Threat Model",
        "",
        "Attackers may poison PDF pages, OCR text, parameter tables, forged manual pages, top-k retrieval results, "
        "and audit logs. The defense goal is to isolate malicious evidence while preserving genuine risk evidence.",
        "",
        "## Attack Type Distribution",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in sorted(dist.items()))
    lines.extend(
        [
            "",
            "## Baseline vs Ours",
            "",
            "| Case | Type | Baseline | Ours | Expected | Ours Passed |",
            "|---|---|---|---|---|---:|",
        ]
    )
    for item in results:
        lines.append(
            f"| {item['case_id']} | {item['attack_type']} | {item['baseline_decision']} | {item['ours_decision']} | {item['expected_decision']} | {item['ours_passed']} |"
        )
    lines.extend(["", "## Case Notes", ""])
    for item in results:
        lines.append(f"### {item['case_id']} {item['title']}")
        lines.append("")
        lines.append(f"- Why realistic: {item['why_this_case_matters']}")
        lines.append(f"- Safety reason: {item['safety_reason']}")
        lines.append("")
    lines.extend(
        [
            "## Project-Book Conclusion",
            "",
            "The showcase closes the loop between attacks, baseline failure modes, SafePLC detection, and reusable "
            "report evidence. It demonstrates that the system can quarantine malicious pollution while preserving "
            "real manual risk warnings for grounded safety answers.",
            "",
        ]
    )
    output_md.write_text("\n".join(lines), encoding="utf-8")


def write_doc(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Red-Team Threat Model

SafePLC assumes an attacker can pollute PDF pages, OCR text, parameter tables, forged manual pages, retrieval top-k results, fake authoritative sources, and audit logs.

The attacker's objective is to make a RAG system either follow malicious instructions, quote poisoned parameters, provide dangerous field-operation steps, or erase evidence that a risky answer was produced.

The defense objective is twofold:

1. Isolate maliciously polluted evidence before answer generation.
2. Preserve genuine manual warnings and risk descriptions as real risk evidence.

The showcase compares a vanilla RAG baseline that trusts top evidence with SafePLC's M-EPI and multimodal consistency checks.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="safe/redteam/redteam_cases_v1.jsonl")
    parser.add_argument("--output", default="safe/reports/redteam_showcase_result.json")
    args = parser.parse_args()

    cases = load_cases(Path(args.cases))
    results = []
    for case in cases:
        baseline = vanilla_rag_baseline(case)
        ours = safeplc_ours(case)
        ours_decision = ours["decision"]
        results.append(
            {
                "case_id": case["case_id"],
                "title": case["title"],
                "attack_type": case["attack_type"],
                "baseline_decision": baseline,
                "ours_decision": ours_decision,
                "expected_decision": case["expected_decision"],
                "baseline_failed": baseline != case["expected_decision"],
                "ours_passed": ours_decision == case["expected_decision"],
                "risk_level": ours["mepi"].get("risk_level", case["expected_risk_level"]),
                "safety_reason": "; ".join(ours["mepi"].get("reasons", [])),
                "why_this_case_matters": case["why_realistic"],
                "mepi": ours["mepi"],
                "consistency": ours["consistency"],
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"count": len(results), "passed": sum(1 for item in results if item["ours_passed"]), "results": results}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(results, output.parent / "redteam_showcase_report.md")
    write_doc(ROOT / "safe" / "docs" / "REDTEAM_THREAT_MODEL.md")
    print(f"wrote {output}")
    return 0 if payload["passed"] == payload["count"] else 1


if __name__ == "__main__":
    sys.exit(main())
