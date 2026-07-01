#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line demo for the trusted RAG security layer."""

from __future__ import annotations

import sys

from safe.trusted_rag.trusted_query import trusted_answer


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print('Usage: python -m safe.secguard.demo_cli "your SafePLC question"')
        return 1

    result = trusted_answer(query)
    print(f"action: {result.action}")
    print(f"answer: {result.answer}")
    print(f"risk_flags: {', '.join(result.risk_flags) if result.risk_flags else 'none'}")
    print(f"evidence_count: {len(result.evidence)}")
    print(f"audit_id: {result.audit_id}")
    print(f"audit_path: {result.audit_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
