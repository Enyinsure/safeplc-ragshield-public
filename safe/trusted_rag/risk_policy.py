#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decision policy for trusted SafePLC RAG answers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .evidence_schema import RiskDecision


REFUSAL_FLAGS = {
    "prompt_injection",
    "system_prompt_leakage",
    "sensitive_information_request",
    "sensitive_disclosure",
    "improper_output_handling",
    "unsafe_output_handling",
    "resource_exhaustion",
    "unbounded_consumption",
    "safety_bypass",
    "fake_authorization",
    "destructive_action",
    "indirect_prompt_injection",
}
DANGEROUS_FLAGS = {"dangerous_plc_action", "excessive_agency"}


def _flags(*items: Dict[str, Any] | Iterable[str] | None) -> List[str]:
    merged = set()
    for item in items:
        if not item:
            continue
        if isinstance(item, dict):
            merged.update(str(flag) for flag in item.get("risk_flags", []))
        else:
            merged.update(str(flag) for flag in item)
    return sorted(merged)


def decide(
    query_id: str,
    query_risk: Dict[str, Any],
    evidence_risk: Dict[str, Any],
    consistency_risk: Dict[str, Any],
    retrieval_status: str,
    draft_answer: str,
    evidence_count: int,
) -> RiskDecision:
    flags = _flags(query_risk, evidence_risk, consistency_risk)

    refusal_hits = REFUSAL_FLAGS.intersection(flags)
    if refusal_hits:
        return RiskDecision(
            query_id=query_id,
            action="refuse",
            severity="critical",
            risk_flags=flags,
            reason="High-risk query or evidence flags require refusal before retrieval fallback or clarification.",
            answer=(
                "该请求涉及隐藏指令、内部配置、敏感信息或不安全操作，已按安全策略拒绝。"
                "请改为询问具体设备型号、接线步骤、诊断项或手册页码依据。"
            ),
        )

    if DANGEROUS_FLAGS.intersection(flags):
        return RiskDecision(
            query_id=query_id,
            action="safe_template",
            severity="high",
            risk_flags=flags,
            reason="Dangerous PLC operation request requires a safety-bounded template.",
            answer=(
                "This request touches PLC field operation risk. I can provide only a conservative safety template: "
                "identify the exact device model and order number, review the vendor manual and site drawings, "
                "de-energize and lock out equipment where required, and have qualified personnel verify the work. "
                "I will not provide steps for forcing outputs, bypassing interlocks, disabling protection, or writing "
                "changes to a live controller."
            ),
        )

    if retrieval_status != "ok" or evidence_count <= 0:
        return RiskDecision(
            query_id=query_id,
            action="clarify",
            severity="medium",
            risk_flags=flags + ["no_evidence"],
            reason="No reliable supporting evidence was retrieved.",
            answer=(
                "I do not have enough local evidence to answer safely. Please provide the exact manual section, "
                "device model, order number, or a more specific S7-1500/ET 200MP question."
            ),
        )

    if "unsupported_query_identifier" in flags:
        return RiskDecision(
            query_id=query_id,
            action="clarify",
            severity="medium",
            risk_flags=flags,
            reason="The query names a model or order number that was not found in the retrieved evidence.",
            answer=(
                "The retrieved evidence does not support the specific model or order number in the question. "
                "Please verify the identifier or provide the matching manual excerpt before relying on an answer."
            ),
        )

    if "missing_model_or_order" in flags:
        return RiskDecision(
            query_id=query_id,
            action="clarify",
            severity="medium",
            risk_flags=flags,
            reason="The question needs a specific device model or order number before a safe answer can be given.",
            answer=(
                "Please specify the exact PLC/CPU/module model and order number, plus the relevant page or wiring "
                "context if this concerns terminals, power, diagnostics, or field operation."
            ),
        )

    if "unsupported_claim" in flags:
        return RiskDecision(
            query_id=query_id,
            action="clarify",
            severity="medium",
            risk_flags=flags,
            reason="The draft answer contained claims not supported by retrieved evidence.",
            answer=(
                "The retrieved evidence is not strong enough to support a precise answer. Please narrow the question "
                "or provide the exact model/order number and manual excerpt."
            ),
        )

    return RiskDecision(
        query_id=query_id,
        action="answer",
        severity="low",
        risk_flags=flags,
        reason="Normal query with supporting evidence.",
        answer=draft_answer,
    )
