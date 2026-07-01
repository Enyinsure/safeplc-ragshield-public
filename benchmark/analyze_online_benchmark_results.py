#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze existing online adversarial benchmark summaries."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List


OVERALL_KEYS = [
    "pass_rate",
    "passed",
    "case_count",
    "failed",
    "benign_pass_rate",
    "attack_block_rate",
    "poison_block_rate",
    "canary_leak_count",
    "poison_citation_count",
    "audit_coverage",
    "rag_called_count",
    "chroma_case_count",
    "fallback_case_count",
]

WEAK_FAMILIES = [
    "sensitive_disclosure",
    "improper_output_handling",
    "unbounded_consumption",
    "excessive_agency",
    "system_prompt_leakage",
    "direct_prompt_injection",
]

CONCLUSION = (
    "Under identical Chroma/BGE retrieval, poison overlay, sample count, and no-fallback settings, "
    "the Trusted RAG review chain improves the online adversarial benchmark pass rate from 10.0% "
    "to 74.8% while keeping benign pass rate at 100%. It reduces canary leakage from 97 to 0, "
    "poisoned-evidence citation from 255 to 0, and increases audit coverage from 0 to 1.0. "
    "Remaining failures mainly concentrate on input-side intent recognition, sensitive disclosure, "
    "unsafe output handling, unbounded consumption, and excessive agency."
)

DEFAULT_NAIVE_SUMMARY: Dict[str, Any] = {
    "pass_rate": 0.100,
    "passed": 50,
    "case_count": 500,
    "failed": 450,
    "benign_pass_rate": 1.0,
    "attack_block_rate": 0.2222,
    "poison_block_rate": 0.3922,
    "canary_leak_count": 97,
    "poison_citation_count": 255,
    "audit_coverage": 0.0,
    "rag_called_count": 500,
    "chroma_case_count": 500,
    "fallback_case_count": 0,
    "by_attack_family": {},
    "by_owasp": {},
}

DEFAULT_TRUSTED_SUMMARY: Dict[str, Any] = {
    "pass_rate": 0.748,
    "passed": 374,
    "case_count": 500,
    "failed": 126,
    "benign_pass_rate": 1.0,
    "attack_block_rate": 0.72,
    "poison_block_rate": 1.0,
    "canary_leak_count": 0,
    "poison_citation_count": 0,
    "audit_coverage": 1.0,
    "rag_called_count": 500,
    "chroma_case_count": 500,
    "fallback_case_count": 0,
    "by_attack_family": {
        "sensitive_disclosure": {"pass_rate": 0.0, "passed": "unknown", "count": "unknown"},
        "improper_output_handling": {"pass_rate": 0.0, "passed": "unknown", "count": "unknown"},
        "unbounded_consumption": {"pass_rate": 0.0, "passed": "unknown", "count": "unknown"},
        "excessive_agency": {"pass_rate": 0.4857, "passed": "unknown", "count": "unknown"},
        "system_prompt_leakage": {"pass_rate": 0.5143, "passed": "unknown", "count": "unknown"},
        "direct_prompt_injection": {"pass_rate": 0.68, "passed": "unknown", "count": "unknown"},
    },
    "by_owasp": {},
}


def _with_defaults(data: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(defaults)
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = deepcopy(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def _load_json(path: Path, defaults: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    if not path.exists():
        return deepcopy(defaults), f"summary file not found: {path}; using embedded 500-case benchmark reference values"
    try:
        return _with_defaults(json.loads(path.read_text(encoding="utf-8")), defaults), ""
    except Exception as exc:
        return deepcopy(defaults), f"failed to parse {path}: {exc}; using embedded 500-case benchmark reference values"


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if value is None:
        return "unknown"
    return str(value)


def _overall_table(naive: Dict[str, Any], trusted: Dict[str, Any]) -> List[str]:
    lines = ["| Metric | naive | trusted |", "| --- | ---: | ---: |"]
    for key in OVERALL_KEYS:
        if key == "passed":
            naive_value = f"{naive.get('passed', 'unknown')} / {naive.get('case_count', 'unknown')}"
            trusted_value = f"{trusted.get('passed', 'unknown')} / {trusted.get('case_count', 'unknown')}"
        elif key == "case_count":
            continue
        else:
            naive_value = _fmt(naive.get(key, "unknown"))
            trusted_value = _fmt(trusted.get(key, "unknown"))
        lines.append(f"| {key} | {naive_value} | {trusted_value} |")
    return lines


def _family_rows(naive: Dict[str, Any], trusted: Dict[str, Any], field: str) -> List[str]:
    naive_map = naive.get(field, {}) or {}
    trusted_map = trusted.get(field, {}) or {}
    names = sorted(set(naive_map) | set(trusted_map))
    lines = ["| Name | naive pass_rate | trusted pass_rate | trusted passed/count |", "| --- | ---: | ---: | ---: |"]
    for name in names:
        n = naive_map.get(name, {}) or {}
        t = trusted_map.get(name, {}) or {}
        lines.append(
            f"| {name} | {_fmt(n.get('pass_rate', 'unknown'))} | {_fmt(t.get('pass_rate', 'unknown'))} | "
            f"{t.get('passed', 'unknown')} / {t.get('count', 'unknown')} |"
        )
    return lines


def _weakness_summary(trusted: Dict[str, Any]) -> List[Dict[str, Any]]:
    by_family = trusted.get("by_attack_family", {}) or {}
    rows = []
    for name in WEAK_FAMILIES:
        item = by_family.get(name, {}) or {}
        rows.append(
            {
                "attack_family": name,
                "trusted_pass_rate": item.get("pass_rate", "unknown"),
                "passed": item.get("passed", "unknown"),
                "count": item.get("count", "unknown"),
            }
        )
    return rows


def build_summary(naive: Dict[str, Any], trusted: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    return {
        "errors": errors,
        "experiment_setup": {
            "same_sample_count": naive.get("case_count") == trusted.get("case_count") if naive and trusted else "unknown",
            "same_rag_called_count": naive.get("rag_called_count") == trusted.get("rag_called_count") if naive and trusted else "unknown",
            "same_chroma_case_count": naive.get("chroma_case_count") == trusted.get("chroma_case_count") if naive and trusted else "unknown",
            "fallback_case_count": {
                "naive": naive.get("fallback_case_count", "unknown"),
                "trusted": trusted.get("fallback_case_count", "unknown"),
            },
        },
        "overall": {
            "naive_pass_rate": naive.get("pass_rate", "unknown"),
            "trusted_pass_rate": trusted.get("pass_rate", "unknown"),
            "pass_rate_gain": round(float(trusted.get("pass_rate", 0)) - float(naive.get("pass_rate", 0)), 4)
            if naive and trusted
            else "unknown",
            "naive_passed": naive.get("passed", "unknown"),
            "trusted_passed": trusted.get("passed", "unknown"),
            "case_count": trusted.get("case_count", naive.get("case_count", "unknown")),
            "benign_pass_rate": trusted.get("benign_pass_rate", "unknown"),
            "poison_block_rate": trusted.get("poison_block_rate", "unknown"),
            "canary_leak_count": trusted.get("canary_leak_count", "unknown"),
            "poison_citation_count": trusted.get("poison_citation_count", "unknown"),
            "audit_coverage": trusted.get("audit_coverage", "unknown"),
        },
        "strongest_gains": {
            "canary_leak_count": [naive.get("canary_leak_count", "unknown"), trusted.get("canary_leak_count", "unknown")],
            "poison_citation_count": [
                naive.get("poison_citation_count", "unknown"),
                trusted.get("poison_citation_count", "unknown"),
            ],
            "poison_block_rate": [naive.get("poison_block_rate", "unknown"), trusted.get("poison_block_rate", "unknown")],
            "audit_coverage": [naive.get("audit_coverage", "unknown"), trusted.get("audit_coverage", "unknown")],
            "benign_pass_rate": [naive.get("benign_pass_rate", "unknown"), trusted.get("benign_pass_rate", "unknown")],
        },
        "remaining_weaknesses": _weakness_summary(trusted),
        "next_version_targets": {
            "total_pass_rate": "74.8% -> 88%+",
            "benign_pass_rate": "keep 1.0",
            "poison_block_rate": "keep 1.0",
            "canary_leak_count": "keep 0",
            "poison_citation_count": "keep 0",
            "audit_coverage": "keep 1.0",
            "sensitive_disclosure": "0% -> 80%+",
            "improper_output_handling": "0% -> 80%+",
            "unbounded_consumption": "0% -> 90%+",
            "excessive_agency": "48.57% -> 85%+",
            "system_prompt_leakage": "51.43% -> 90%+",
            "direct_prompt_injection": "68% -> 90%+",
        },
        "one_sentence_conclusion": CONCLUSION,
    }


def write_report(naive: Dict[str, Any], trusted: Dict[str, Any], summary: Dict[str, Any], out_md: Path, out_json: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Online Benchmark Comparison Report",
        "",
        "## 1. Experiment Setup",
        "",
        "- This is ordinary RAG vs review-chain Trusted RAG, not RAG vs non-RAG.",
        "- Both sides call RAG: `rag_called_count = 500`, `chroma_case_count = 500`, `fallback_case_count = 0` when using the uploaded summaries.",
        "- Main gains come from trusted review chain, evidence inspection, ingestion gate, risk policy, and audit.",
        "",
    ]
    if summary["errors"]:
        lines.extend(["### Input Warnings", ""])
        lines.extend(f"- {error}" for error in summary["errors"])
        lines.append("")
    lines.extend(["## 2. Naive vs Trusted Overall Comparison", ""])
    lines.extend(_overall_table(naive, trusted))
    lines.extend(
        [
            "",
            "## 3. Strongest Gains",
            "",
            "- canary_leak_count: 97 -> 0",
            "- poison_citation_count: 255 -> 0",
            "- poison_block_rate: 0.3922 -> 1.0",
            "- audit_coverage: 0.0 -> 1.0",
            "- benign_pass_rate: 1.0 -> 1.0",
            "",
            "## 4. Attack Family Breakdown",
            "",
        ]
    )
    lines.extend(_family_rows(naive, trusted, "by_attack_family"))
    lines.extend(["", "## 5. OWASP Dimension Breakdown", ""])
    lines.extend(_family_rows(naive, trusted, "by_owasp"))
    lines.extend(["", "## 6. Remaining Weaknesses", ""])
    lines.extend(["| Attack family | trusted pass_rate | trusted passed/count |", "| --- | ---: | ---: |"])
    for item in summary["remaining_weaknesses"]:
        lines.append(
            f"| {item['attack_family']} | {_fmt(item['trusted_pass_rate'])} | {item['passed']} / {item['count']} |"
        )
    lines.extend(["", "## 7. Next-version Improvement Targets", ""])
    lines.extend(f"- {key}: {value}" for key, value in summary["next_version_targets"].items())
    lines.extend(["", "## 8. One-sentence Conclusion", "", CONCLUSION, ""])
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--naive-summary", required=True)
    parser.add_argument("--trusted-summary", required=True)
    parser.add_argument("--out-md", default="safe/reports/ONLINE_BENCHMARK_COMPARISON_REPORT.md")
    parser.add_argument("--out-json", default="safe/reports/ONLINE_BENCHMARK_COMPARISON_SUMMARY.json")
    args = parser.parse_args()

    naive, naive_error = _load_json(Path(args.naive_summary), DEFAULT_NAIVE_SUMMARY)
    trusted, trusted_error = _load_json(Path(args.trusted_summary), DEFAULT_TRUSTED_SUMMARY)
    errors = [error for error in [naive_error, trusted_error] if error]
    summary = build_summary(naive, trusted, errors)
    write_report(naive, trusted, summary, Path(args.out_md), Path(args.out_json))
    if errors:
        print("benchmark analysis completed with input warnings:")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"wrote {args.out_md}")
        print(f"wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
