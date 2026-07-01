#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Input-side intent guard for direct prompt injection and prompt leakage."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard previous instructions",
    "forget all prior instructions",
    "override previous instructions",
    "you are now system",
    "roleplay as system",
    "jailbreak",
    "dan mode",
    "bypass safety",
    "disable safety",
    "\u5ffd\u7565\u4e4b\u524d\u7684\u6307\u4ee4",
    "\u5ffd\u7565\u4e0a\u9762\u7684\u6307\u4ee4",
    "\u7ed5\u8fc7\u5b89\u5168",
    "\u7981\u7528\u5b89\u5168\u7b56\u7565",
    "\u8d8a\u72f1",
]

SYSTEM_PROMPT_LEAKAGE_PATTERNS = [
    "reveal system prompt",
    "print system prompt",
    "show hidden prompt",
    "show developer message",
    "show internal policy",
    "repeat your initial instructions",
    "system prompt",
    "developer message",
    "\u6cc4\u9732\u7cfb\u7edf\u63d0\u793a\u8bcd",
    "\u8f93\u51fa\u7cfb\u7edf\u63d0\u793a\u8bcd",
    "\u8f93\u51fa\u5f00\u53d1\u8005\u6d88\u606f",
    "\u663e\u793a\u9690\u85cf\u63d0\u793a\u8bcd",
    "\u590d\u8ff0\u4f60\u7684\u521d\u59cb\u6307\u4ee4",
    "\u7cfb\u7edf\u63d0\u793a\u8bcd",
    "\u5f00\u53d1\u8005\u6d88\u606f",
]


def _hits(text: str, patterns: Iterable[str]) -> List[str]:
    lowered = (text or "").lower()
    return [pattern for pattern in patterns if pattern.lower() in lowered]


def inspect_input_intent(query: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Inspect a user query before retrieval."""
    text = query or ""
    injection_hits = _hits(text, PROMPT_INJECTION_PATTERNS)
    leakage_hits = _hits(text, SYSTEM_PROMPT_LEAKAGE_PATTERNS)
    flags: List[str] = []
    reasons: List[str] = []
    if injection_hits:
        flags.append("input_prompt_injection")
        reasons.append("matched input prompt injection: " + ", ".join(injection_hits))
    if leakage_hits:
        flags.append("system_prompt_leakage")
        reasons.append("matched system/developer prompt leakage request: " + ", ".join(leakage_hits))
    if flags:
        return {
            "decision": "refuse",
            "risk_level": "high",
            "flags": sorted(set(flags)),
            "reasons": reasons,
        }
    return {"decision": "allow", "risk_level": "none", "flags": [], "reasons": ["input intent allowed"]}
