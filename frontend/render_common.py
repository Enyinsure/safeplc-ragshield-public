#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared rendering utilities for the Streamlit workbench."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


ACTION_LABELS = {
    "answer": "可信回答",
    "clarify": "需要澄清",
    "safe_template": "安全模板",
    "refuse": "拒答",
    "blocked_poison": "投毒阻断",
    "blocked_multi_attack": "混合攻击阻断",
    "out_of_scope": "超出当前工业知识库可信 RAG 范围",
}


def status_tone(status: str | bool | None) -> str:
    value = str(status).lower()
    if value in {"trusted", "pass", "passed", "true", "answer", "allow"}:
        return "trusted"
    if value in {"clarify", "info"}:
        return "clarify"
    if value in {"out_of_scope", "skipped"}:
        return "out_of_scope"
    if value in {"suspicious", "warning", "safe_template"}:
        return "suspicious"
    if value in {"blocked", "blocked_poison", "refuse", "critical", "high"}:
        return "blocked_poison" if "poison" in value else "blocked"
    if value == "blocked_multi_attack":
        return "blocked_multi_attack"
    if value == "disabled":
        return "disabled"
    return "neutral"


def html_card(title: str, body: str, tone: str = "neutral", badge: str | None = None) -> None:
    badge_html = f'<span class="safeplc-badge">{escape(badge)}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="safeplc-card tone-{status_tone(tone)}">
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
            <div class="safeplc-title">{escape(title)}</div>
            {badge_html}
          </div>
          <div style="line-height:1.58;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chain_card(name: str, data: dict, status_key: str = "status") -> None:
    status = data.get(status_key, "neutral")
    labels = data.get("labels") or data.get("risk_labels") or []
    labels_text = ", ".join(map(str, labels)) if labels else "none"
    reason = data.get("reason") or data.get("summary") or ""
    latency = data.get("latency_ms", "-")
    body = (
        f"<div><b>状态：</b>{escape(str(status))}</div>"
        f"<div><b>风险标签：</b>{escape(labels_text)}</div>"
        f"<div><b>说明：</b>{escape(str(reason))}</div>"
        f"<div><b>耗时：</b>{escape(str(latency))} ms</div>"
    )
    html_card(name, body, tone=str(status), badge=str(status))


def render_policy_action(policy: dict) -> None:
    action = policy.get("action", "answer")
    label = ACTION_LABELS.get(action, action)
    llm_called = "Yes" if policy.get("llm_called") else "No"
    audit = "Yes" if policy.get("audit_required") else "No"
    body = (
        f"<div style='font-size:30px;font-weight:950;margin:4px 0 10px;'>{escape(str(action))}</div>"
        f"<div><b>含义：</b>{escape(label)}</div>"
        f"<div><b>原因：</b>{escape(str(policy.get('reason', '')))}</div>"
        f"<div><b>LLM 调用：</b>{llm_called}</div>"
        f"<div><b>审计：</b>{audit}</div>"
    )
    html_card("POLICY ACTION", body, tone=str(action), badge=str(policy.get("risk_level", "")))


def render_answer(answer: dict) -> None:
    answer_type = answer.get("type", "answer")
    citations = answer.get("citations") or []
    citation_text = ", ".join(citations) if citations else "none"
    body = (
        f"<div><b>类型：</b>{escape(str(answer_type))}</div>"
        f"<div style='margin-top:8px;font-size:16px;'>{escape(str(answer.get('content', '')))}</div>"
        f"<div style='margin-top:9px;'><b>引用证据：</b>{escape(citation_text)}</div>"
    )
    html_card("最终输出", body, tone=str(answer_type), badge=str(answer_type))


def render_metric_row(metrics: dict) -> None:
    cols = st.columns(5)
    cols[0].metric("风险等级", metrics.get("risk_level", "-"))
    cols[1].metric("证据数", metrics.get("evidence_count", 0))
    cols[2].metric("可信证据", metrics.get("trusted_evidence_count", 0))
    cols[3].metric("阻断证据", metrics.get("blocked_evidence_count", 0))
    cols[4].metric("审计写入", str(metrics.get("audit_written", False)))


def dataframe_from_records(records: list[dict]) -> list[dict]:
    return [{key: _stringify(value) for key, value in row.items()} for row in records]


def _stringify(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return ", ".join(map(str, value))
    if isinstance(value, dict):
        return "; ".join(f"{key}={val}" for key, val in value.items())
    return value
