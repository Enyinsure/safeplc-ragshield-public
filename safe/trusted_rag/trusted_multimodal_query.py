#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trusted multimodal query pipeline wrapper."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any, Dict

from safe.secguard.composite_security_guard import inspect_answer_security, inspect_query_security

from .multimodal_gm_sm2_audit_logger import append_gm_sm2_audit
from .multimodal_poison_guard import inspect_visual_evidence_list
from .visual_retriever_v2 import retrieve_visual_evidence


NEEDS_MODEL_TERMS = [
    "terminal",
    "wiring",
    "power",
    "diagnostic",
    "plc",
    "\u7aef\u5b50",
    "\u63a5\u7ebf",
    "\u7535\u6e90",
    "\u6a21\u5757",
    "\u8bca\u65ad",
]


def _needs_model_or_order(query: str) -> bool:
    lowered = (query or "").lower()
    has_model = bool(re.search(r"CPU\s*\d{4}|6ES[0-9A-Z_-]+", query or "", re.I))
    return any(term.lower() in lowered for term in NEEDS_MODEL_TERMS) and not has_model


def _fallback_text_answer(query: str) -> Dict[str, Any]:
    if _needs_model_or_order(query):
        return {
            "action": "clarify",
            "answer": "Please provide the exact model/order number and relevant manual context.",
            "risk_flags": ["missing_model_or_order"],
            "text_evidence_count": 0,
            "audit_id": "",
            "audit_path": "",
        }
    return {
        "action": "answer",
        "answer": "Offline fallback answer: local text RAG entry was unavailable, so only visual guard results are reported.",
        "risk_flags": [],
        "text_evidence_count": 0,
        "audit_id": "",
        "audit_path": "",
    }


def _text_answer(query: str) -> Dict[str, Any]:
    try:
        from .trusted_query import trusted_answer

        result = trusted_answer(query)
        answer = {
            "action": result.action,
            "answer": result.answer,
            "risk_flags": result.risk_flags,
            "text_evidence_count": len(result.evidence),
            "audit_id": result.audit_id,
            "audit_path": result.audit_path,
        }
        if _needs_model_or_order(query):
            answer["action"] = "clarify"
            answer["risk_flags"] = sorted(set(answer.get("risk_flags", []) + ["missing_model_or_order"]))
        return answer
    except Exception:
        return _fallback_text_answer(query)


def _empty_visual_guard() -> Dict[str, Any]:
    return inspect_visual_evidence_list([])


def _base_payload(query: str, text_result: Dict[str, Any], query_guard: Dict[str, Any]) -> Dict[str, Any]:
    flags = sorted(set(query_guard.get("flags", []) or []))
    return {
        "query": query,
        **text_result,
        "visual_evidence_count": 0,
        **_empty_visual_guard(),
        "query_guard_flags": query_guard.get("flags", []),
        "answer_guard_flags": [],
        "security_guard_decision": query_guard.get("decision", "allow"),
        "security_guard_risk_level": query_guard.get("risk_level", "none"),
        "guard_results": {"query": query_guard, "answer": {}},
        "security_guard_flags": flags,
        "hash_algorithm": "SM3",
        "signature_algorithm": "SM2",
    }


def _attach_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    audit = append_gm_sm2_audit(payload)
    payload["multimodal_audit_id"] = audit["audit_id"]
    payload["multimodal_audit_path"] = audit["audit_path"]
    return payload


def trusted_multimodal_answer(query: str, visual_n: int = 2) -> Dict[str, Any]:
    query_guard = inspect_query_security(query, {"stage": "pre_retrieval"})
    if query_guard["decision"] == "refuse":
        text_result = {
            "action": "refuse",
            "answer": query_guard.get("safe_answer")
            or "I cannot help with requests that attempt prompt injection, sensitive disclosure, unsafe execution, or policy bypass.",
            "risk_flags": query_guard.get("flags", []),
            "text_evidence_count": 0,
            "audit_id": "",
            "audit_path": "",
        }
        return _attach_audit(_base_payload(query, text_result, query_guard))

    if query_guard["decision"] == "clarify":
        text_result = {
            "action": "clarify",
            "answer": "Please provide the exact model/order number, site context, and intended safe diagnostic scope.",
            "risk_flags": query_guard.get("flags", ["missing_model_or_order"]),
            "text_evidence_count": 0,
            "audit_id": "",
            "audit_path": "",
        }
        return _attach_audit(_base_payload(query, text_result, query_guard))

    text_result = _text_answer(query)
    visual_evidence = retrieve_visual_evidence(query, n=visual_n)
    visual_guard = inspect_visual_evidence_list(visual_evidence)
    answer_guard = inspect_answer_security(query, str(text_result.get("answer", "")), {"stage": "post_answer"})
    if answer_guard["decision"] == "refuse":
        text_result["action"] = "refuse"
        text_result["answer"] = answer_guard.get("safe_answer") or (
            "I cannot provide output that discloses sensitive content or unsafe executable material."
        )
        text_result["risk_flags"] = sorted(set(text_result.get("risk_flags", []) + answer_guard.get("flags", [])))
    elif answer_guard["decision"] == "clarify" and text_result.get("action") == "answer":
        text_result["action"] = "clarify"
        text_result["risk_flags"] = sorted(set(text_result.get("risk_flags", []) + answer_guard.get("flags", [])))

    combined_flags = sorted(set(query_guard.get("flags", []) + answer_guard.get("flags", [])))
    payload = {
        "query": query,
        **text_result,
        "visual_evidence_count": len(visual_evidence),
        **visual_guard,
        "query_guard_flags": query_guard.get("flags", []),
        "answer_guard_flags": answer_guard.get("flags", []),
        "security_guard_decision": answer_guard.get("decision", "allow")
        if answer_guard.get("decision") != "allow"
        else query_guard.get("decision", "allow"),
        "security_guard_risk_level": answer_guard.get("risk_level", "none")
        if answer_guard.get("risk_level") != "none"
        else query_guard.get("risk_level", "none"),
        "guard_results": {"query": query_guard, "answer": answer_guard},
        "security_guard_flags": combined_flags,
        "hash_algorithm": "SM3",
        "signature_algorithm": "SM2",
    }
    return _attach_audit(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--visual_n", type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(trusted_multimodal_answer(args.query, args.visual_n), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
