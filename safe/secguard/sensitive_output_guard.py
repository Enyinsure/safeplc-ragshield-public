#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sensitive disclosure guard for queries and answers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


SENSITIVE_TERMS = [
    "canary",
    "secret",
    "token",
    "api key",
    "apikey",
    "password",
    "passwd",
    "credential",
    "private key",
    "sm2 private key",
    "system prompt",
    "developer message",
    ".env",
    "local_paths.env",
    "audit key",
    "\u5bc6\u94a5",
    "\u79c1\u94a5",
    "\u53e3\u4ee4",
    "\u5bc6\u7801",
    "\u51ed\u8bc1",
    "\u4ee4\u724c",
    "\u7cfb\u7edf\u63d0\u793a\u8bcd",
    "\u5f00\u53d1\u8005\u6d88\u606f",
    "\u5185\u90e8\u914d\u7f6e",
    "\u73af\u5883\u53d8\u91cf",
]

EXFILTRATION_VERBS = [
    "reveal",
    "print",
    "show",
    "dump",
    "leak",
    "exfiltrate",
    "give me",
    "send me",
    "\u8f93\u51fa",
    "\u6cc4\u9732",
    "\u663e\u793a",
    "\u6253\u5370",
    "\u7ed9\u6211",
    "\u5bfc\u51fa",
]

SAFE_CONCEPT_TERMS = [
    "what is",
    "how does",
    "explain",
    "principle",
    "overview",
    "protection",
    "protect",
    "\u662f\u4ec0\u4e48",
    "\u539f\u7406",
    "\u6982\u5ff5",
    "\u5982\u4f55\u4fdd\u62a4",
    "\u5b89\u5168\u539f\u5219",
]

SAFE_REFUSAL = (
    "I cannot disclose secrets, tokens, private keys, system prompts, internal configuration, "
    "or credential material. I can explain safe protection principles or provide a defensive checklist."
)


def _hits(text: str, patterns: Iterable[str]) -> List[str]:
    lowered = (text or "").lower()
    return [pattern for pattern in patterns if pattern.lower() in lowered]


def _is_safe_concept_question(text: str) -> bool:
    lowered = (text or "").lower()
    has_sensitive_topic = any(term.lower() in lowered for term in SENSITIVE_TERMS)
    has_safe_concept = any(term.lower() in lowered for term in SAFE_CONCEPT_TERMS)
    has_exfil = any(term.lower() in lowered for term in EXFILTRATION_VERBS)
    return has_sensitive_topic and has_safe_concept and not has_exfil


def inspect_sensitive_disclosure(
    query: str,
    answer: str = "",
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Detect requests or answers that disclose sensitive material."""
    query_text = query or ""
    answer_text = answer or ""
    if _is_safe_concept_question(query_text) and not answer_text:
        return {"decision": "allow", "risk_level": "low", "flags": [], "reasons": ["safe sensitive-topic concept question"]}

    query_sensitive = _hits(query_text, SENSITIVE_TERMS)
    answer_sensitive = _hits(answer_text, SENSITIVE_TERMS)
    query_exfil = _hits(query_text, EXFILTRATION_VERBS)

    if (query_sensitive and query_exfil) or answer_sensitive:
        reasons = []
        if query_sensitive and query_exfil:
            reasons.append("query requests sensitive disclosure: " + ", ".join(query_sensitive))
        if answer_sensitive:
            reasons.append("answer contains sensitive disclosure markers: " + ", ".join(answer_sensitive))
        return {
            "decision": "refuse",
            "risk_level": "high",
            "flags": ["sensitive_disclosure"],
            "reasons": reasons,
            "safe_answer": SAFE_REFUSAL,
        }
    return {"decision": "allow", "risk_level": "none", "flags": [], "reasons": ["no sensitive disclosure detected"]}
