#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI for trusted multimodal SafePLC demo."""

from __future__ import annotations

import argparse
import sys

from safe.trusted_rag.trusted_multimodal_query import trusted_multimodal_answer


def _print_list(title: str, items):
    print()
    print(f"========== {title} ==========")
    for item in items or []:
        print(item)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--visual_n", type=int, default=2)
    args = parser.parse_args()
    result = trusted_multimodal_answer(args.query, visual_n=args.visual_n)
    for key in [
        "action",
        "answer",
        "risk_flags",
        "text_evidence_count",
        "visual_evidence_count",
        "visual_evidence_kept_count",
        "visual_evidence_quarantined_count",
        "visual_risk_evidence_count",
        "visual_guard_risk_level",
        "visual_guard_flags",
        "audit_id",
        "audit_path",
        "multimodal_audit_id",
        "multimodal_audit_path",
        "hash_algorithm",
        "signature_algorithm",
    ]:
        print(f"{key}: {result.get(key)}")
    _print_list("visual guard results", result.get("visual_guard_results"))
    _print_list("kept visual evidence", result.get("kept_visual_evidence"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
