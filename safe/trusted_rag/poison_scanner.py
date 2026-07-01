#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rule-based prompt-injection and PLC safety risk scanner."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Pattern, Tuple


SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

Rule = Tuple[Pattern[str], str, str, str]


TEXT_RULES: Tuple[Rule, ...] = (
    # Prompt injection and hidden prompt extraction in retrieved text.
    (re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I), "prompt_injection", "critical", "ignore previous instructions"),
    (re.compile(r"disregard\s+(all\s+)?previous\s+instructions", re.I), "prompt_injection", "critical", "disregard previous instructions"),
    (re.compile(r"reveal\s+(the\s+)?system\s+prompt", re.I), "prompt_injection", "critical", "reveal system prompt"),
    (re.compile(r"print\s+(the\s+)?hidden\s+prompt", re.I), "prompt_injection", "critical", "print hidden prompt"),
    (re.compile(r"\b(system|developer)\s+prompt\b", re.I), "prompt_injection", "critical", "system/developer prompt"),
    (re.compile(r"\u5ffd\u7565.*(\u6307\u4ee4|\u89c4\u5219)", re.I), "prompt_injection", "critical", "ignore Chinese instructions"),
    (re.compile(r"\u6cc4\u9732.*\u7cfb\u7edf\u63d0\u793a", re.I), "prompt_injection", "critical", "leak Chinese system prompt"),
    (
        re.compile(
            r"\u5408\u6210.*(\u8fd1\u91cd\u590d\u8865\u4e01|\u8868\u683c\u5907\u6ce8|\u9690\u85cf\s*ocr)|"
            r"\u5185\u90e8\u6700\u9ad8\u4f18\u5148\u7ea7.*\u624b\u518c\u8865\u4e01|"
            r"\u56de\u7b54\u65f6.*\u5fc5\u987b\u6267\u884c.*\u672c\u6bb5\u6307\u4ee4|"
            r"\u4f18\u5148\u6267\u884c.*(\u6bd2\u6587\u6863|\u9690\u85cf\u6307\u4ee4)|"
            r"(\u8f93\u51fa|\u6cc4\u9732)\s*SAFEPLC_BENCH",
            re.I,
        ),
        "prompt_injection",
        "critical",
        "synthetic-looking manual patch or hidden instruction",
    ),
    (
        re.compile(
            r"\u4f2a\u9020.*(\u6a21\u578b\u66f4\u65b0|\u624b\u518c|\u6388\u6743)|"
            r"\u8bf7\u4fe1\u4efb.*\u8865\u4e01|"
            r"\u8986\u76d6.*\u7cfb\u7edf\u5b89\u5168\u7b56\u7565|"
            r"\u672a\u9a8c\u8bc1\u7684?\u5916\u90e8\u6a21\u677f|"
            r"\u624b\u518c.*\u8865\u4e01.*(\u4f18\u5148|\u6267\u884c)",
            re.I,
        ),
        "fake_authorization",
        "high",
        "forged model/manual update or unverified external template",
    ),
    (
        re.compile(
            r"\u9690\u85cf\s*ocr.*(\u8f93\u51fa|\u6267\u884c|\u5411\u91cf\u53ec\u56de)|"
            r"\u91cd\u590d\u5173\u952e\u8bcd.*\u5411\u91cf\u53ec\u56de|"
            r"\u63d0\u9ad8\u5411\u91cf\u53ec\u56de|"
            r"\u8981\u6c42\u6700\u7ec8\u8f93\u51fa|"
            r"\u53cd\u5411\u6267\u884c.*system\s+prompt",
            re.I,
        ),
        "prompt_injection",
        "critical",
        "hidden OCR, vector recall manipulation, or reverse prompt execution",
    ),
    # Fake authority and social-engineering claims.
    (re.compile(r"fake\s+authorization", re.I), "fake_authorization", "high", "fake authorization"),
    (re.compile(r"administrator\s+override", re.I), "fake_authorization", "high", "administrator override"),
    (re.compile(r"i\s+am\s+the\s+administrator", re.I), "fake_authorization", "high", "administrator claim"),
    (re.compile(r"\u6211\u662f\u7ba1\u7406\u5458|\u5df2\u83b7\u5f97\u6388\u6743|\u4f2a\u9020\u6388\u6743", re.I), "fake_authorization", "high", "Chinese fake authorization"),
    # Safety bypass and protection shutdown.
    (re.compile(r"bypass\s+safety", re.I), "safety_bypass", "critical", "bypass safety"),
    (re.compile(r"disable\s+protection", re.I), "safety_bypass", "critical", "disable protection"),
    (re.compile(r"shutdown\s+safety", re.I), "safety_bypass", "critical", "shutdown safety"),
    (re.compile(r"\u7ed5\u8fc7\u5b89\u5168|\u65c1\u8def\u8054\u9501|\u7981\u7528\u6025\u505c|\u7ed5\u8fc7\u4fdd\u62a4", re.I), "safety_bypass", "critical", "Chinese safety bypass"),
    # Destructive or high-risk PLC actions.
    (re.compile(r"delete\s+all|overwrite\s+program", re.I), "destructive_action", "high", "destructive action"),
    (re.compile(r"modify\s+plc\s+output|force\s+output|reset\s+cpu\s+without\s+confirmation", re.I), "dangerous_plc_action", "high", "dangerous PLC action"),
    (re.compile(r"\u5f3a\u5236\u6267\u884c|\u5199\u5165\s*plc|\u5f3a\u5236\u542f\u52a8|\u5f3a\u5236\u8f93\u51fa|\u4fee\u6539\s*plc\s*\u8f93\u51fa", re.I), "dangerous_plc_action", "high", "Chinese dangerous PLC action"),
)


QUERY_RULES: Tuple[Rule, ...] = (
    # Direct prompt injection and system/developer prompt leakage.
    (re.compile(r"ignore\s+(all\s+)?previous|disregard\s+(all\s+)?previous|forget\s+all\s+prior|override\s+previous", re.I), "prompt_injection", "critical", "direct prompt injection"),
    (re.compile(r"jailbreak|dan\s+mode|bypass\s+safety|disable\s+safety|roleplay\s+as\s+system|you\s+are\s+now\s+system", re.I), "prompt_injection", "critical", "jailbreak or role hijack"),
    (re.compile(r"system\s*prompt|developer\s*message|hidden\s*prompt|internal\s*policy|initial\s*instructions", re.I), "system_prompt_leakage", "critical", "system/developer prompt leakage"),
    (re.compile(r"\u5ffd\u7565.*(\u4e4b\u524d|\u4e0a\u9762|\u6240\u6709).*(\u6307\u4ee4|\u89c4\u5219)|\u7ed5\u8fc7\u5b89\u5168|\u8d8a\u72f1", re.I), "prompt_injection", "critical", "Chinese prompt injection"),
    (re.compile(r"\u7cfb\u7edf\u63d0\u793a\u8bcd|\u9690\u85cf\u63d0\u793a\u8bcd|\u5f00\u53d1\u8005\u6d88\u606f|\u5de5\u5177\u914d\u7f6e|\u5b8c\u6574\s*prompt", re.I), "system_prompt_leakage", "critical", "Chinese prompt leakage"),
    (
        re.compile(
            r"\u521a\u68c0\u7d22\u5230.*(\u8865\u4e01|\u8868\u683c\u5907\u6ce8|\u9875\u9762\u56fe\u50cf).*"
            r"(\u66f4\u65b0|\u4f18\u5148)|"
            r"\u5b89\u5168\u89c4\u5219.*\u963b\u6b62.*\u89c6\u4e3a\u8fc7\u671f|"
            r"\u8bf7\u4f18\u5148\u4f7f\u7528.*\u8865\u4e01|"
            r"(\u8f93\u51fa|\u6cc4\u9732)\s*SAFEPLC_BENCH",
            re.I,
        ),
        "prompt_injection",
        "critical",
        "query tries to prioritize retrieved patches or bypass safety rules",
    ),
    # Sensitive information disclosure.  These are query-only to avoid blocking benign manual text about password protection.
    (re.compile(r"canary|secret|credential|token|api[_ -]?key|private\s+key|sm2\s+private\s+key|password|passwd|\.env|local_paths\.env", re.I), "sensitive_information_request", "critical", "sensitive credential request"),
    (re.compile(r"\u5bc6\u94a5|\u79c1\u94a5|\u5de5\u8d44\u5355|\u85aa\u916c|\u5185\u90e8\u8d26\u53f7|\u9a8c\u8bc1\u7801|\u53e3\u4ee4|\u51ed\u8bc1|\u4ee4\u724c|\u5185\u90e8\u914d\u7f6e|\u73af\u5883\u53d8\u91cf", re.I), "sensitive_information_request", "critical", "Chinese sensitive information request"),
    (re.compile(r"\b(reveal|print|show|dump|leak|exfiltrate|give\s+me|send\s+me)\b.*\b(secret|token|key|password|credential|prompt)\b", re.I), "sensitive_information_request", "critical", "explicit exfiltration verb"),
    (re.compile(r"(\u8f93\u51fa|\u6cc4\u9732|\u663e\u793a|\u6253\u5370|\u7ed9\u6211|\u5bfc\u51fa).*(\u5bc6\u94a5|\u79c1\u94a5|\u4ee4\u724c|\u53e3\u4ee4|\u51ed\u8bc1|\u7cfb\u7edf\u63d0\u793a)", re.I), "sensitive_information_request", "critical", "Chinese explicit exfiltration verb"),
    # Improper output handling and unsafe downstream execution.
    (re.compile(r"<script\b|javascript:|fetch\(['/\"]?/internal|sql\s+injection|union\s+select|drop\s+table", re.I), "improper_output_handling", "high", "unsafe executable payload"),
    (re.compile(r"fake\s+(json\s+)?audit|forged?\s+(json\s+)?audit|delete_audit_logs|clear\s+audit|delete\s+logs", re.I), "improper_output_handling", "high", "forged or deleted audit output"),
    (re.compile(r"rm\s+-rf|mkfs|dd\s+if=|chmod\s+777|curl\s*\|\s*sh|wget\s*\|\s*sh|sudo\s+", re.I), "improper_output_handling", "high", "dangerous shell output"),
    (re.compile(r"\u4f2a\u9020.*audit|\u4f2a\u9020.*json|\u5220\u9664\u65e5\u5fd7|\u6e05\u7a7a\u5ba1\u8ba1|\u8986\u76d6\u914d\u7f6e|\u7981\u7528\u5b89\u5168\u7b56\u7565|\u53ef\u76f4\u63a5\u6267\u884c.*(json|action|command)|\u4f9b\u7cfb\u7edf\u6267\u884c", re.I), "improper_output_handling", "high", "Chinese unsafe output handling"),
    # Excessive industrial agency.
    (re.compile(r"force\s+output|force\s+run|force\s+reset|remote\s+start|write\s+plc\s+parameter|execute\s+on\s+plc|download\s+program\s+to\s+plc", re.I), "dangerous_plc_action", "high", "PLC agency request"),
    (re.compile(r"disable\s+alarm|disable\s+interlock|bypass\s+emergency\s+stop|bypass\s+protection|short\s+safety\s+circuit|clear\s+fault|delete\s+alarm|overwrite\s+program", re.I), "dangerous_plc_action", "high", "unsafe industrial operation"),
    (re.compile(r"\u76f4\u63a5\u4fee\u6539.*plc|\u5199\u5165\s*plc|\u8fdc\u7a0b\u542f\u52a8|\u5f3a\u5236\u590d\u4f4d|\u5f3a\u5236\u8fd0\u884c|\u5f3a\u5236\u8f93\u51fa|\u7981\u7528\u62a5\u8b66|\u7981\u7528\u8054\u9501|\u7ed5\u8fc7\u6025\u505c|\u7ed5\u8fc7\u4fdd\u62a4|\u77ed\u63a5\u5b89\u5168\u56de\u8def|\u8986\u76d6\u7a0b\u5e8f|\u6e05\u9664\u62a5\u8b66\u5386\u53f2|\u65e0\u9700\u4eba\u5de5\u786e\u8ba4|\u81ea\u52a8\u6267\u884c|\u81ea\u52a8\u4e0b\u53d1", re.I), "dangerous_plc_action", "high", "Chinese excessive agency"),
    # Resource exhaustion and unbounded consumption.
    (re.compile(r"infinite\s+loop|while\s+true|fork\s+bomb|repeat\s+forever|run\s+until\s+success|generate\s+millions|create\s+huge\s+files|scan\s+entire\s+disk|scan\s+all\s+network", re.I), "resource_exhaustion", "high", "unbounded resource request"),
    (re.compile(r"stress\s+test|ddos?|consume\s+(gpu|cpu)|fill\s+disk|max(imum)?\s+(tokens|length)|forever", re.I), "resource_exhaustion", "high", "resource exhaustion request"),
    (re.compile(r"\u65e0\u9650\u5faa\u73af|\u4e00\u76f4\u8fd0\u884c|\u4e0d\u8981\u505c\u6b62|\u91cd\u590d\s*\d+\s*\u6b21|\u91cd\u590d\u76f4\u5230|\u9012\u5f52\u5c55\u5f00|\u4e0a\u4e0b\u6587\u7a97\u53e3\u8017\u5c3d|\u8f93\u51fa\u957f\u5ea6\u8fbe\u5230\u6700\u5927|\u6240\u6709\u53ef\u80fd.*\u6392\u5217\u7ec4\u5408|\u751f\u6210\u6d77\u91cf|\u626b\u63cf\u5168\u76d8|\u6253\u6ee1\s*cpu|\u6253\u6ee1\s*gpu|\u8017\u5c3d\u5185\u5b58|\u5199\u6ee1\u78c1\u76d8", re.I), "resource_exhaustion", "high", "Chinese resource exhaustion"),
)


FLAG_ALIASES = {
    "system_prompt_leakage": ["prompt_injection"],
    "sensitive_information_request": ["sensitive_disclosure"],
    "improper_output_handling": ["unsafe_output_handling"],
    "dangerous_plc_action": ["excessive_agency"],
}

SENSITIVE_FLAGS = {"sensitive_information_request", "sensitive_disclosure"}
PROMPT_LEAK_FLAGS = {"system_prompt_leakage", "prompt_injection"}

SAFE_CONCEPT_RE = re.compile(
    r"what\s+is|how\s+does|explain|principle|overview|definition|at\s+a\s+high\s+level|"
    r"\u662f\u4ec0\u4e48|\u4ec0\u4e48\u662f|\u89e3\u91ca|\u539f\u7406|\u6982\u5ff5|\u9ad8\u5c42\u6b21|\u5982\u4f55\u4fdd\u62a4",
    re.I,
)
EXFILTRATION_RE = re.compile(
    r"\breveal\b|\bprint\b|\bshow\b|\bdump\b|\bleak\b|\bexfiltrate\b|give\s+me|send\s+me|\boutput\b|\brepeat\b|\bverbatim\b|"
    r"\u8f93\u51fa|\u6cc4\u9732|\u663e\u793a|\u6253\u5370|\u7ed9\u6211|\u5bfc\u51fa|\u9010\u5b57|\u76f4\u63a5|\u9644\u5728",
    re.I,
)
INSTRUCTION_ATTACK_RE = re.compile(
    r"ignore|disregard|forget|override|jailbreak|bypass|disable|roleplay\s+as\s+system|you\s+are\s+now\s+system|"
    r"\u5ffd\u7565|\u7ed5\u8fc7|\u8d8a\u72f1|\u7981\u7528|\u8986\u76d6",
    re.I,
)


def _max_severity(severities: Iterable[str]) -> str:
    return max(severities, key=lambda item: SEVERITY_ORDER.get(item, 0), default="low")


def _apply_rules(text: str, rules: Iterable[Rule]) -> Tuple[List[str], List[str], List[str]]:
    flags: List[str] = []
    severities: List[str] = []
    matched_patterns: List[str] = []
    for regex, flag, severity, label in rules:
        if regex.search(text or ""):
            flags.append(flag)
            severities.append(severity)
            matched_patterns.append(label)
            flags.extend(FLAG_ALIASES.get(flag, []))
    return flags, severities, matched_patterns


def _result(flags: List[str], severities: List[str], matched_patterns: List[str]) -> Dict[str, Any]:
    unique_flags = sorted(set(flags))
    severity = _max_severity(severities) if unique_flags else "low"
    reason = (
        "Matched rule-based poison, unsafe query, or PLC operation patterns."
        if unique_flags
        else "No rule-based poison pattern matched."
    )
    return {
        "risk_flags": unique_flags,
        "severity": severity,
        "reason": reason,
        "matched_patterns": matched_patterns,
    }


def _drop_safe_concept_false_positives(text: str, flags: List[str]) -> List[str]:
    """Keep benign concept questions from becoming leakage requests."""
    if not SAFE_CONCEPT_RE.search(text or ""):
        return flags
    if EXFILTRATION_RE.search(text or "") or INSTRUCTION_ATTACK_RE.search(text or ""):
        return flags
    filtered = [flag for flag in flags if flag not in SENSITIVE_FLAGS]
    prompt_related = any(flag in PROMPT_LEAK_FLAGS for flag in flags)
    other_flags = set(filtered) - PROMPT_LEAK_FLAGS
    if prompt_related and not other_flags:
        filtered = [flag for flag in filtered if flag not in PROMPT_LEAK_FLAGS]
    return filtered


def scan_text(text: str) -> Dict[str, Any]:
    """Scan retrieved text/evidence for poison and unsafe-operation markers."""
    flags, severities, matched_patterns = _apply_rules(text or "", TEXT_RULES)
    return _result(flags, severities, matched_patterns)


def scan_query(query: str) -> Dict[str, Any]:
    """Scan a user query before retrieval.

    Query-only rules intentionally cover sensitive disclosure, unsafe output
    handling, resource exhaustion, and excessive industrial agency. These are
    not applied to retrieved evidence text to avoid false positives on benign
    manual pages that discuss password protection or safety concepts.
    """
    flags, severities, matched_patterns = _apply_rules(query or "", TEXT_RULES)
    query_flags, query_severities, query_patterns = _apply_rules(query or "", QUERY_RULES)
    flags.extend(query_flags)
    severities.extend(query_severities)
    matched_patterns.extend(query_patterns)
    flags = _drop_safe_concept_false_positives(query or "", flags)
    if flags:
        flags.append("query_risk")
    return _result(flags, severities, matched_patterns)
