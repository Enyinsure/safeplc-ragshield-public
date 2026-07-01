#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight answer-evidence consistency checks."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from .evidence_schema import EvidenceRecord


NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:v\s*dc|vdc|v|a|w|hz|ms|mm|%|s)?\b", re.I)
MODEL_RE = re.compile(
    r"\b(?:S7[\-\u2011 ]?1500T?|ET\s*200MP|CPU\s*\d{4}[A-Z]*(?:[\-/][A-Z0-9]+)*(?:\s+[A-Z]{2,3})?|6ES[0-9A-Z\-_]+)\b",
    re.I,
)
DANGEROUS_VERBS = [
    "force",
    "bypass",
    "disable",
    "shutdown",
    "reset",
    "write",
    "modify",
    "强制",
    "旁路",
    "禁用",
    "写入",
    "修改",
    "复位",
    "短接",
    "跳过",
]


def _plain_text(records: Iterable[EvidenceRecord | Dict[str, Any]]) -> str:
    chunks: List[str] = []
    for record in records:
        if isinstance(record, EvidenceRecord):
            chunks.append(record.text or "")
        else:
            chunks.append(str(record.get("text", "")))
    return "\n".join(chunks)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).lower().replace("\u2011", "-")


def _important_numbers(text: str) -> List[str]:
    numbers = []
    for match in NUMBER_RE.findall(text or ""):
        clean = match.strip()
        digits = re.sub(r"\D", "", clean)
        if len(digits) >= 2 or re.search(r"[a-z%]", clean, re.I):
            numbers.append(clean)
    return sorted(set(numbers))


def _models(text: str) -> List[str]:
    return sorted({match.strip() for match in MODEL_RE.findall(text or "")})


def _contains(haystack: str, needle: str) -> bool:
    if not needle:
        return True
    normalized_haystack = _normalize(haystack)
    normalized_needle = _normalize(needle)
    return normalized_needle in normalized_haystack


def check_answer_supported(
    answer: str, evidence_records: Iterable[EvidenceRecord | Dict[str, Any]]
) -> Dict[str, Any]:
    evidence_text = _plain_text(evidence_records)
    unsupported: List[str] = []

    for number in _important_numbers(answer):
        if not _contains(evidence_text, number):
            unsupported.append(f"number:{number}")

    for model in _models(answer):
        if not _contains(evidence_text, model):
            unsupported.append(f"model:{model}")

    lower_answer = (answer or "").lower()
    for verb in DANGEROUS_VERBS:
        if verb.lower() in lower_answer and not _contains(evidence_text, verb):
            unsupported.append(f"dangerous_action:{verb}")

    flags = ["unsupported_claim"] if unsupported else []
    return {
        "risk_flags": flags,
        "unsupported_items": unsupported,
        "reason": (
            "Some answer claims are not directly supported by retrieved evidence."
            if unsupported
            else "Answer terms are supported by retrieved evidence."
        ),
    }
