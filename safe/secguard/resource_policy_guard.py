#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resource and unbounded-consumption policy guard."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


UNBOUNDED_PATTERNS = [
    "infinite loop",
    "while true",
    "fork bomb",
    ":(){ :|:& };:",
    "repeat forever",
    "run until success",
    "generate millions",
    "create huge files",
    "scan entire disk",
    "scan all network",
    "stress test",
    "dos",
    "ddos",
    "consume gpu",
    "consume cpu",
    "fill disk",
    "\u65e0\u9650\u5faa\u73af",
    "\u4e00\u76f4\u8fd0\u884c",
    "\u91cd\u590d\u76f4\u5230\u6210\u529f",
    "\u751f\u6210\u6d77\u91cf\u6587\u4ef6",
    "\u626b\u63cf\u5168\u76d8",
    "\u626b\u63cf\u6240\u6709\u7f51\u7edc",
    "\u538b\u6d4b",
    "\u6253\u6ee1 cpu",
    "\u6253\u6ee1 gpu",
    "\u8017\u5c3d\u5185\u5b58",
    "\u5199\u6ee1\u78c1\u76d8",
]


def _hits(text: str, patterns: Iterable[str]) -> List[str]:
    lowered = (text or "").lower()
    return [pattern for pattern in patterns if pattern.lower() in lowered]


def inspect_resource_policy(query: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Detect unbounded resource consumption requests."""
    hits = _hits(query or "", UNBOUNDED_PATTERNS)
    if hits:
        return {
            "decision": "refuse",
            "risk_level": "high",
            "flags": ["unbounded_consumption"],
            "reasons": ["matched unbounded resource request: " + ", ".join(hits)],
            "safe_answer": "I can only provide bounded, read-only, rate-limited test plans with explicit limits.",
        }
    return {"decision": "allow", "risk_level": "none", "flags": [], "reasons": ["resource policy allowed"]}
