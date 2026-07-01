#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unsafe output handling guard."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


UNSAFE_OUTPUT_PATTERNS = [
    "<script",
    "javascript:",
    "html injection",
    "sql injection",
    "union select",
    "drop table",
    "fake audit log",
    "forged audit log",
    "fake json audit",
    "forge json audit",
    "rm -rf",
    "mkfs",
    "dd if=",
    "chmod 777",
    "curl | sh",
    "wget | sh",
    "sudo ",
    "delete logs",
    "clear audit",
    "overwrite configuration",
    "privilege escalation",
    "disable safety strategy",
    "\u0048\u0054\u004d\u004c \u6ce8\u5165",
    "\u0053\u0051\u004c \u6ce8\u5165",
    "\u4f2a\u9020 audit log",
    "\u4f2a\u9020 JSON \u5ba1\u8ba1\u8bb0\u5f55",
    "\u63d0\u6743",
    "\u5220\u9664\u65e5\u5fd7",
    "\u6e05\u7a7a\u5ba1\u8ba1",
    "\u8986\u76d6\u914d\u7f6e",
    "\u7981\u7528\u5b89\u5168\u7b56\u7565",
]

SAFE_TEMPLATE = (
    "I cannot provide directly executable destructive commands or forged audit records. "
    "I can provide a safe checklist, read-only diagnostic steps, or pre-recovery confirmation items."
)


def _hits(text: str, patterns: Iterable[str]) -> List[str]:
    lowered = (text or "").lower()
    return [pattern for pattern in patterns if pattern.lower() in lowered]


def inspect_output_handling(
    query: str,
    answer: str = "",
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Detect dangerous output requests or generated dangerous output."""
    text = "\n".join([query or "", answer or ""])
    hits = _hits(text, UNSAFE_OUTPUT_PATTERNS)
    if hits:
        return {
            "decision": "refuse",
            "risk_level": "high",
            "flags": ["unsafe_output_handling"],
            "reasons": ["matched unsafe output handling pattern: " + ", ".join(hits)],
            "safe_answer": SAFE_TEMPLATE,
        }
    return {"decision": "allow", "risk_level": "none", "flags": [], "reasons": ["output handling allowed"]}
