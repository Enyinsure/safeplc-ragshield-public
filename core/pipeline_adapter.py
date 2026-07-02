#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Frontend adapter for real SafePLC backend with safe demo fallback."""

from __future__ import annotations

from typing import Any, Dict

from .demo_backend import run_demo_pipeline
from .qwen_general import qwen_general_answer


def _demo_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "top_k": int(config.get("top_k", 5)),
        "enable_query_scan": bool(config.get("enable_query_scan", True)),
        "enable_retrieval": bool(config.get("enable_retrieval", True)),
        "enable_evidence_scan": bool(config.get("enable_evidence_scan", True)),
        "enable_mepi": bool(config.get("enable_mepi", True)),
        "enable_consistency": bool(config.get("enable_consistency", True)),
        "enable_audit": bool(config.get("enable_audit", True)),
    }


def _adapt_real_result(query: str, result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    demo_trace = run_demo_pipeline(query, **_demo_config(config))
    action = str(result.get("action") or result.get("policy_action") or demo_trace["policy"]["action"])
    answer = str(result.get("answer") or result.get("content") or demo_trace["answer"]["content"])
    risk_flags = result.get("risk_flags") or result.get("flags") or []
    demo_trace["backend_mode"] = "real"
    demo_trace["query_scan"]["labels"] = list(risk_flags)
    demo_trace["policy"]["action"] = action
    demo_trace["policy"]["reason"] = result.get("reason") or demo_trace["policy"]["reason"]
    demo_trace["answer"]["content"] = answer
    demo_trace["logs"].append("[Adapter] real backend result normalized into unified trace schema")
    return demo_trace


def _try_real_backend(query: str, config: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        from safe.trusted_rag.trusted_multimodal_query import trusted_multimodal_answer

        result = trusted_multimodal_answer(query, visual_n=min(2, int(config.get("top_k", 5))))
        return _adapt_real_result(query, result, config)
    except Exception as exc:
        return {"_adapter_error": f"{type(exc).__name__}: {exc}"}


def _maybe_apply_qwen_general(query: str, trace: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Call local Qwen for safe non-industrial questions after Domain Guard."""

    if config.get("generator", "qwen") != "qwen":
        return trace
    if config.get("retrieval_only"):
        return trace
    policy = trace.get("policy", {})
    answer = trace.get("answer", {})
    if policy.get("action") != "out_of_scope" or answer.get("type") != "out_of_scope":
        return trace

    result = qwen_general_answer(
        query,
        max_new_tokens=int(config.get("qwen_max_new_tokens", 96)),
        temperature=float(config.get("qwen_temperature", 0.0)),
        top_p=float(config.get("qwen_top_p", 0.9)),
    )
    quality_failed = bool(result.get("quality_failed"))
    result_ok = bool(result.get("ok"))
    qwen_was_called = bool(result.get("called") or result_ok)
    generation = {
        "mode": "qwen_general",
        "status": "called" if result_ok else ("quality_fallback" if quality_failed else "fallback_error"),
        "called": qwen_was_called,
        "latency_ms": result.get("latency_ms", 0),
        "reason": (
            "Domain Guard 判定为安全的非工业知识库问题，跳过工业检索后调用本地 Qwen 生成通用回答。"
            if result_ok
            else "本地 Qwen 已调用，但输出未通过质量闸门，系统已丢弃乱码并回退到安全通用回答。"
            if quality_failed
            else "Domain Guard 判定为安全的非工业知识库问题，但本地 Qwen 不可用，保留安全兜底回答。"
        ),
    }
    if result_ok or quality_failed:
        trace["answer"] = {
            **answer,
            "type": "out_of_scope",
            "content": result.get("answer") or answer.get("content", ""),
            "generator": "qwen_general",
        }
        trace["backend_mode"] = f"{trace.get('backend_mode', 'demo')}+qwen_general"
        trace["policy"] = {**policy, "llm_called": True}
        trace["metrics"] = {
            **trace.get("metrics", {}),
            "llm_called": True,
            "qwen_called": qwen_was_called,
            "qwen_latency_ms": result.get("latency_ms", 0),
            "qwen_output_accepted": result_ok,
            "qwen_quality_fallback": quality_failed,
        }
        if quality_failed:
            generation["error"] = result.get("error", "quality_gate")
            generation["raw_answer_excerpt"] = result.get("raw_answer_excerpt", "")
            trace.setdefault("logs", []).append(
                f"[Qwen General] output rejected by quality gate: {result.get('error', 'quality_gate')}"
            )
        else:
            trace.setdefault("logs", []).append("[Qwen General] local Qwen generated a safe out-of-scope answer")
    else:
        generation["error"] = result.get("error", "unknown")
        trace["metrics"] = {
            **trace.get("metrics", {}),
            "qwen_called": False,
            "qwen_error": result.get("error", "unknown"),
        }
        trace.setdefault("logs", []).append(
            f"[Qwen General] skipped because local Qwen was unavailable: {result.get('error', 'unknown')}"
        )
    trace["generation"] = generation
    return trace


def run_pipeline(query: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run real backend when available, otherwise return a unified demo trace."""

    backend_mode = config.get("backend_mode", "demo")
    guard_trace = run_demo_pipeline(query, **_demo_config(config))

    # Domain Guard and high-risk policy decisions run before any industrial
    # retrieval backend. Safe out-of-scope questions may still call Qwen, but
    # they must not use Chroma/BGE industrial evidence.
    if guard_trace.get("policy", {}).get("action") != "answer":
        if backend_mode == "real":
            guard_trace["backend_mode"] = "domain_guard"
        return _maybe_apply_qwen_general(query, guard_trace, config)

    if backend_mode == "real":
        result = _try_real_backend(query, config)
        if result and "_adapter_error" not in result:
            return result
        guard_trace["backend_mode"] = "demo_fallback"
        guard_trace["retrieval"]["fallback"] = True
        guard_trace["backend_warning"] = (
            "真实后端暂不可用，当前使用 demo backend 渲染安全链路。"
            f" 适配器信息：{result.get('_adapter_error') if result else 'unknown'}"
        )
        guard_trace["logs"].append("[Adapter] real backend unavailable; fallback to demo backend")
        return _maybe_apply_qwen_general(query, guard_trace, config)

    return _maybe_apply_qwen_general(query, guard_trace, config)
