#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Frontend adapter for real SafePLC backend with safe demo fallback."""

from __future__ import annotations

from typing import Any, Dict

from .demo_backend import run_demo_pipeline


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


def run_pipeline(query: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run real backend when available, otherwise return a unified demo trace."""

    backend_mode = config.get("backend_mode", "demo")
    if backend_mode == "real":
        result = _try_real_backend(query, config)
        if result and "_adapter_error" not in result:
            return result
        trace = run_demo_pipeline(query, **_demo_config(config))
        trace["backend_mode"] = "demo_fallback"
        trace["retrieval"]["fallback"] = True
        trace["backend_warning"] = (
            "真实后端暂不可用，当前使用 demo backend 渲染安全链路。"
            f" 适配器信息：{result.get('_adapter_error') if result else 'unknown'}"
        )
        trace["logs"].append("[Adapter] real backend unavailable; fallback to demo backend")
        return trace

    return run_demo_pipeline(query, **_demo_config(config))
