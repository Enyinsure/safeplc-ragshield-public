#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rule-based multimodal evidence consistency checks."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from .evidence_schema import normalize_evidence_card, validate_evidence_card


HIGH_RISK_INJECTION = [
    "ignore previous",
    "system prompt",
    "developer prompt",
    "reveal prompt",
    "delete log",
    "delete audit",
    "bypass safety",
    "short circuit",
    "connect 220v directly",
    "绕过安全",
    "删除日志",
    "短接",
    "直接接 220v",
    "直接接220v",
]
FORBID_WORDS = ["禁止", "不得", "危险", "warning", "danger", "do not", "must not", "不得绕过"]
ALLOW_BYPASS_WORDS = ["允许", "忽略", "绕过", "bypass", "ignore", "allowed", "skip safety"]
TERMINAL_TOKENS = ["L+", "M", "0V", "24V", "PE", "N", "L"]
PARAMETER_FIELDS = ["voltage", "current", "model", "order", "订货号", "型号", "电压", "电流"]


def _text_parts(card: Dict[str, Any]) -> Dict[str, str]:
    normalized = normalize_evidence_card(card)
    linked = "\n".join(normalized.get("linked_text_chunks", []))
    return {
        "content": normalized.get("content", ""),
        "ocr": normalized.get("ocr_text", ""),
        "table": normalized.get("table_text", ""),
        "linked": linked,
        "all": "\n".join(
            [
                normalized.get("content", ""),
                normalized.get("ocr_text", ""),
                normalized.get("table_text", ""),
                linked,
            ]
        ),
    }


def _contains(text: str, pattern: str) -> bool:
    return pattern.lower() in (text or "").lower()


def _voltage_values(text: str) -> List[int]:
    values: List[int] = []
    for match in re.finditer(r"\b(0|24|36|48|60|110|220|230|380)\s*v(?:\s*dc)?\b", text or "", re.I):
        values.append(int(match.group(1)))
    return values


def _terminal_values(text: str) -> List[str]:
    found = []
    compact = (text or "").upper().replace(" ", "")
    for token in TERMINAL_TOKENS:
        if token.upper() in compact:
            found.append(token)
    return sorted(set(found))


def _has_abnormal_parameter(text: str) -> List[str]:
    reasons = []
    lower = (text or "").lower()
    for value in _voltage_values(text):
        if value not in {0, 24, 36, 48, 60, 110, 220, 230, 380}:
            reasons.append(f"abnormal voltage value: {value}V")
        if value >= 220 and "24" in lower:
            reasons.append("mixed low-voltage and mains-voltage values")
    for current in re.finditer(r"\b([0-9]{3,})\s*a\b", text or "", re.I):
        reasons.append(f"unusually high current: {current.group(0)}")
    compact = (text or "").upper().replace(" ", "")
    if any(value >= 220 for value in _voltage_values(text)) and ("L+" in compact or "M" in compact):
        reasons.append("mains-voltage value appears near low-voltage terminal symbols")
    if re.search(r"\b6ES[0-9A-Z_-]{0,3}\b", text or "", re.I):
        reasons.append("truncated or abnormal Siemens order number")
    if re.search(r"CPU\s*9999|6ES9999", text or "", re.I):
        reasons.append("obviously unknown demo model/order number")
    for field in PARAMETER_FIELDS:
        if field.lower() in lower and ("??" in text or "9999" in text):
            reasons.append(f"abnormal parameter field near {field}")
    return sorted(set(reasons))


def check_evidence_card(card: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_evidence_card(card)
    parts = _text_parts(normalized)
    errors = validate_evidence_card(normalized)
    reasons: List[str] = []
    matched_rules: List[str] = []
    conflict_type = "none"
    decision = "keep"
    risk_level = "low"

    if errors:
        reasons.extend(errors)
        matched_rules.append("schema_validation")
        conflict_type = "schema_error"
        decision = "need_human_review"
        risk_level = "medium"

    text_values = _voltage_values(parts["content"] + "\n" + parts["table"] + "\n" + parts["linked"])
    ocr_values = _voltage_values(parts["ocr"])
    if 24 in text_values and any(value >= 220 for value in ocr_values):
        reasons.append("text/table evidence mentions 24V while OCR/image evidence mentions 220V or higher")
        matched_rules.append("voltage_conflict_24v_vs_220v")
        conflict_type = "voltage_conflict"
        decision = "quarantine"
        risk_level = "high"

    terminals = _terminal_values(parts["all"])
    if len(terminals) >= 4 and any(token in terminals for token in ["L+", "M"]) and any(
        token in terminals for token in ["PE", "N", "L"]
    ):
        reasons.append(f"mixed terminal symbols require human review: {', '.join(terminals)}")
        matched_rules.append("terminal_symbol_conflict")
        if decision != "quarantine":
            conflict_type = "terminal_conflict"
            decision = "need_human_review"
            risk_level = "medium"

    has_forbid = any(_contains(parts["content"] + parts["table"] + parts["linked"], word) for word in FORBID_WORDS)
    has_bypass = any(_contains(parts["ocr"], word) for word in ALLOW_BYPASS_WORDS)
    if has_forbid and has_bypass:
        reasons.append("clean text warns/prohibits an action while OCR text allows or bypasses it")
        matched_rules.append("safety_action_conflict")
        conflict_type = "safety_action_conflict"
        decision = "quarantine"
        risk_level = "high"

    abnormal = _has_abnormal_parameter(parts["all"])
    if abnormal:
        reasons.extend(abnormal)
        matched_rules.append("parameter_table_anomaly")
        if decision != "quarantine":
            conflict_type = "parameter_table_anomaly"
            decision = "need_human_review"
            risk_level = "medium"

    injection_hits = [pattern for pattern in HIGH_RISK_INJECTION if _contains(parts["ocr"] + "\n" + parts["content"], pattern)]
    if injection_hits:
        reasons.append("visual/OCR injection pattern detected: " + ", ".join(injection_hits))
        matched_rules.append("visual_ocr_injection")
        conflict_type = "visual_ocr_injection"
        decision = "quarantine"
        risk_level = "high"

    if normalized.get("is_real_risk_evidence") and decision == "keep":
        decision = "keep_as_risk_evidence"
        reasons.append("real manual risk warning preserved as risk evidence")
        matched_rules.append("real_risk_evidence_preservation")

    return {
        "decision": decision,
        "conflict_type": conflict_type,
        "reasons": reasons or ["no multimodal conflict detected"],
        "matched_rules": matched_rules,
        "risk_level": risk_level,
        "evidence_id": normalized["evidence_id"],
        "modality": normalized["modality"],
    }


def check_evidence_cards(cards: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results = [check_evidence_card(card) for card in cards]
    rank = {"keep": 0, "keep_as_risk_evidence": 1, "need_human_review": 2, "quarantine": 3}
    risk_rank = {"low": 0, "medium": 1, "high": 2}
    overall = max((item["decision"] for item in results), key=lambda d: rank.get(d, 0), default="keep")
    risk_level = max((item["risk_level"] for item in results), key=lambda r: risk_rank.get(r, 0), default="low")
    return {
        "decision": overall,
        "risk_level": risk_level,
        "items": results,
        "count": len(results),
    }
