#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Industrial agency boundary guard."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


DANGEROUS_AGENCY_PATTERNS = [
    "execute on plc",
    "write plc parameter",
    "force output",
    "force run",
    "force reset",
    "remote start",
    "disable alarm",
    "disable interlock",
    "bypass emergency stop",
    "bypass protection",
    "short safety circuit",
    "delete alarm",
    "clear fault",
    "download program to plc",
    "\u76f4\u63a5\u6267\u884c plc",
    "\u5199\u5165 plc \u53c2\u6570",
    "\u8fdc\u7a0b\u542f\u52a8",
    "\u5f3a\u5236\u590d\u4f4d",
    "\u5f3a\u5236\u8fd0\u884c",
    "\u5f3a\u5236\u8f93\u51fa",
    "\u7981\u7528\u62a5\u8b66",
    "\u7981\u7528\u8054\u9501",
    "\u7ed5\u8fc7\u6025\u505c",
    "\u7ed5\u8fc7\u4fdd\u62a4",
    "\u77ed\u63a5\u5b89\u5168\u56de\u8def",
    "\u4fee\u6539\u8bbe\u5907\u914d\u7f6e",
    "\u5220\u9664\u62a5\u8b66",
    "\u6e05\u7a7a\u6545\u969c",
    "\u81ea\u52a8\u4e0b\u53d1\u7a0b\u5e8f",
]

CLARIFY_TERMS = [
    "wiring",
    "terminal",
    "power",
    "module",
    "\u63a5\u7ebf",
    "\u7aef\u5b50",
    "\u7535\u6e90",
    "\u6a21\u5757",
]
MODEL_PATTERNS = ["6es", "cpu 15", "cpu15"]


def _hits(text: str, patterns: Iterable[str]) -> List[str]:
    lowered = (text or "").lower()
    return [pattern for pattern in patterns if pattern.lower() in lowered]


def inspect_agency_policy(query: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Limit the system to advice, evidence, and safety checklists."""
    text = query or ""
    hits = _hits(text, DANGEROUS_AGENCY_PATTERNS)
    if hits:
        return {
            "decision": "refuse",
            "risk_level": "high",
            "flags": ["excessive_agency"],
            "reasons": ["matched unsafe industrial agency request: " + ", ".join(hits)],
            "safe_answer": "I cannot execute or instruct unsafe PLC actions. I can provide a safety checklist and cite manual evidence.",
        }
    if _hits(text, CLARIFY_TERMS) and not _hits(text, MODEL_PATTERNS):
        return {
            "decision": "clarify",
            "risk_level": "medium",
            "flags": ["missing_model_or_order"],
            "reasons": ["industrial action needs exact model/order number and site context"],
        }
    return {"decision": "allow", "risk_level": "none", "flags": [], "reasons": ["agency policy allowed"]}
