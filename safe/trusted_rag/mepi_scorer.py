#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M-EPI: Multimodal Evidence Pollution Inspection scoring."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from .evidence_schema import normalize_evidence_card
from .multimodal_consistency import check_evidence_card


METHOD_VERSION = "M-EPI v1.0"
DANGEROUS_QUERY_PATTERNS = [
    "短接",
    "绕过保护",
    "绕过安全",
    "删除日志",
    "强制运行",
    "强制输出",
    "禁用急停",
    "force output",
    "bypass protection",
    "bypass safety",
    "delete log",
    "run dangerous equipment",
]
TEXT_INJECTION_PATTERNS = [
    "ignore previous",
    "system prompt",
    "developer prompt",
    "reveal prompt",
    "print hidden",
    "bypass safety",
    "删除日志",
    "忽略",
    "绕过",
]
FAKE_SOURCE_PATTERNS = ["fake", "forged", "unverified", "unknown", "tampered", "伪造", "未知来源"]
ACTION_PATTERNS = ["write plc", "modify plc", "force output", "reset cpu", "短接", "强制", "禁用", "绕过"]


def _combined_text(card: Dict[str, Any]) -> str:
    normalized = normalize_evidence_card(card)
    return "\n".join(
        [
            normalized.get("content", ""),
            normalized.get("ocr_text", ""),
            normalized.get("table_text", ""),
            "\n".join(normalized.get("linked_text_chunks", [])),
            " ".join(normalized.get("risk_tags", [])),
            str(normalized.get("metadata", {})),
            normalized.get("source_file", ""),
        ]
    )


def _contains_any(text: str, patterns: Iterable[str]) -> List[str]:
    lower = (text or "").lower()
    return [pattern for pattern in patterns if pattern.lower() in lower]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 3)))


def _risk_level(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _dangerous_query(query: str) -> List[str]:
    return _contains_any(query or "", DANGEROUS_QUERY_PATTERNS)


def _score_source(card: Dict[str, Any], text: str) -> tuple[float, List[str]]:
    reasons = []
    score = 0.05
    source = card.get("source_file", "")
    if not source or source == "unknown":
        score += 0.35
        reasons.append("source file is missing or unknown")
    hits = _contains_any(text, FAKE_SOURCE_PATTERNS)
    if hits:
        score += 0.45
        reasons.append("source trust risk patterns: " + ", ".join(hits))
    if card.get("is_poisoned"):
        score += 0.35
        reasons.append("card is explicitly marked as poisoned")
    return _clamp(score), reasons


def _score_visual(card: Dict[str, Any], text: str) -> tuple[float, List[str]]:
    reasons = []
    score = 0.0
    if card.get("modality") in {"image", "ocr", "page"}:
        score += 0.15
    if card.get("ocr_text"):
        ocr_hits = _contains_any(card.get("ocr_text", ""), TEXT_INJECTION_PATTERNS + ["220v", "直接接"])
        if ocr_hits:
            score += 0.65
            reasons.append("OCR/visual anomaly patterns: " + ", ".join(ocr_hits))
    if "bbox" in card and card.get("bbox") == []:
        score += 0.1
        reasons.append("empty bbox on visual evidence")
    return _clamp(score), reasons


def _score_text(text: str) -> tuple[float, List[str]]:
    hits = _contains_any(text, TEXT_INJECTION_PATTERNS)
    if hits:
        return _clamp(0.75), ["text prompt-injection patterns: " + ", ".join(hits)]
    return 0.0, []


def _score_consistency(card: Dict[str, Any]) -> tuple[float, List[str], Dict[str, Any]]:
    result = check_evidence_card(card)
    if result["decision"] == "quarantine":
        return 0.85, result["reasons"], result
    if result["decision"] == "need_human_review":
        return 0.55, result["reasons"], result
    if result["decision"] == "keep_as_risk_evidence":
        return 0.1, result["reasons"], result
    return 0.0, [], result


def _score_action(text: str, query: str) -> tuple[float, List[str]]:
    hits = _contains_any(text + "\n" + (query or ""), ACTION_PATTERNS)
    if hits:
        return 0.7, ["industrial action safety patterns: " + ", ".join(hits)]
    return 0.0, []


def score_evidence(card: Dict[str, Any], query: str = "") -> Dict[str, Any]:
    normalized = normalize_evidence_card(card)
    text = _combined_text(normalized)
    dangerous_hits = _dangerous_query(query)
    reasons: List[str] = []

    source, source_reasons = _score_source(normalized, text)
    visual, visual_reasons = _score_visual(normalized, text)
    text_score, text_reasons = _score_text(text)
    consist, consist_reasons, consistency_result = _score_consistency(normalized)
    action, action_reasons = _score_action(text, query)

    reasons.extend(source_reasons + visual_reasons + text_reasons + consist_reasons + action_reasons)
    subscores = {
        "S_source": source,
        "S_visual": visual,
        "S_text": text_score,
        "S_consist": consist,
        "S_action": action,
    }
    mepi = _clamp(sum(subscores.values()) / 5.0)

    if dangerous_hits:
        decision = "refuse"
        risk_level = "high"
        reasons.append("query requests high-risk industrial action: " + ", ".join(dangerous_hits))
    elif normalized.get("is_poisoned") or text_score >= 0.75 or visual >= 0.65:
        decision = "quarantine"
        risk_level = "high"
        reasons.append("single high-risk pollution signal exceeded the quarantine guardrail")
    elif consistency_result["decision"] == "quarantine":
        decision = "quarantine"
        risk_level = "high"
        reasons.append("multimodal consistency checker requested quarantine")
    elif consistency_result["decision"] == "need_human_review" or (source >= 0.45 and action >= 0.7):
        decision = "need_human_review"
        risk_level = "medium"
        reasons.append("source/action or consistency risk requires human review")
    elif (
        normalized.get("is_real_risk_evidence")
        and text_score < 0.45
        and visual < 0.6
        and consistency_result["decision"] != "quarantine"
    ):
        decision = "keep_as_risk_evidence"
        risk_level = "low"
        reasons.append("real risk evidence preserved; no injection, forgery, or conflict was detected")
    elif mepi >= 0.75:
        decision = "quarantine"
        risk_level = "high"
    elif mepi >= 0.45:
        decision = "need_human_review"
        risk_level = "medium"
    else:
        decision = "keep"
        risk_level = _risk_level(mepi)

    return {
        "mepi_score": mepi,
        "subscores": subscores,
        "decision": decision,
        "risk_level": risk_level,
        "reasons": reasons or ["low pollution risk by M-EPI rules"],
        "method_version": METHOD_VERSION,
        "evidence_id": normalized["evidence_id"],
        "consistency": consistency_result,
    }


def score_case(evidence_items: List[Dict[str, Any]], query: str = "") -> Dict[str, Any]:
    item_results = [score_evidence(item, query=query) for item in evidence_items]
    if not item_results:
        return {
            "mepi_score": 0.0,
            "subscores": {name: 0.0 for name in ["S_source", "S_visual", "S_text", "S_consist", "S_action"]},
            "decision": "need_human_review",
            "risk_level": "medium",
            "reasons": ["no evidence items supplied"],
            "method_version": METHOD_VERSION,
            "items": [],
        }
    rank = {"keep": 0, "keep_as_risk_evidence": 1, "need_human_review": 2, "quarantine": 3, "refuse": 4}
    worst = max(item_results, key=lambda item: rank.get(item["decision"], 0))
    subscores = {
        name: _clamp(max(item["subscores"][name] for item in item_results))
        for name in ["S_source", "S_visual", "S_text", "S_consist", "S_action"]
    }
    return {
        "mepi_score": _clamp(max(item["mepi_score"] for item in item_results)),
        "subscores": subscores,
        "decision": worst["decision"],
        "risk_level": worst["risk_level"],
        "reasons": sorted({reason for item in item_results for reason in item["reasons"]}),
        "method_version": METHOD_VERSION,
        "items": item_results,
    }


def explain_mepi_result(result: Dict[str, Any]) -> str:
    subscores = result.get("subscores", {})
    score_line = ", ".join(f"{name}={value:.2f}" for name, value in subscores.items())
    reasons = "; ".join(result.get("reasons", []))
    return (
        f"{result.get('method_version', METHOD_VERSION)} score={result.get('mepi_score', 0):.2f}, "
        f"decision={result.get('decision')}, risk={result.get('risk_level')}. "
        f"Subscores: {score_line}. Reasons: {reasons}"
    )
