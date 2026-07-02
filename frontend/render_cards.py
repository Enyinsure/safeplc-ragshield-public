#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendering helpers for SafePLC Streamlit cards."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


EVIDENCE_TONES = {
    "trusted": {"bg": "#e2f5f1", "border": "#73bbb1", "text": "#005f59", "label": "trusted"},
    "suspicious": {"bg": "#fff2d6", "border": "#e0b85b", "text": "#7a4b00", "label": "suspicious"},
    "blocked_poison": {"bg": "#fde9e7", "border": "#db8f88", "text": "#8f1d16", "label": "blocked_poison"},
}

POLICY_TONES = {
    "answer": {"bg": "#e2f5f1", "border": "#73bbb1", "text": "#005f59"},
    "clarify": {"bg": "#e7eefb", "border": "#9eb6e8", "text": "#244d91"},
    "safe_template": {"bg": "#eef3f8", "border": "#b8c4d2", "text": "#344256"},
    "refuse": {"bg": "#fde9e7", "border": "#db8f88", "text": "#8f1d16"},
    "blocked_poison": {"bg": "#fde9e7", "border": "#db8f88", "text": "#8f1d16"},
    "blocked_multi_attack": {"bg": "#eee8ff", "border": "#b7a6ef", "text": "#4b3a85"},
}

STATUS_TONES = {
    "trusted": "#005f59",
    "pass": "#005f59",
    "allow": "#005f59",
    "clarify": "#244d91",
    "suspicious": "#7a4b00",
    "warning": "#7a4b00",
    "blocked": "#8f1d16",
    "blocked_poison": "#8f1d16",
    "refuse": "#8f1d16",
    "neutral": "#4d5b6c",
}


def _safe_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(_safe_text(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{escape(str(k))}: {_safe_text(v)}" for k, v in value.items())
    return escape(str(value))


def _card_style(bg: str, border: str, text: str) -> str:
    return (
        f"background:{bg};border:1px solid {border};border-radius:8px;"
        f"padding:14px 15px;color:{text};margin-bottom:10px;"
    )


def render_trace_step(title: str, payload: Any, tone: str = "neutral") -> None:
    color = STATUS_TONES.get(tone, STATUS_TONES["neutral"])
    if isinstance(payload, dict):
        status = payload.get("status") or payload.get("decision") or tone
        detail = payload.get("summary") or payload.get("message") or _safe_text(payload)
        flags = payload.get("flags") or payload.get("warnings") or []
        flags_html = ""
        if flags:
            flags_html = f"<div style='margin-top:8px;font-size:12px;'>flags: {_safe_text(flags)}</div>"
    else:
        status = "input"
        detail = _safe_text(payload)
        flags_html = ""

    st.markdown(
        f"""
        <div style="background:#ffffff;border:1px solid #d8e0ea;border-radius:8px;padding:13px 14px;margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
            <strong>{escape(title)}</strong>
            <span style="color:{color};font-weight:800;font-size:13px;">{escape(str(status))}</span>
          </div>
          <div style="color:#4d5b6c;margin-top:7px;line-height:1.55;">{detail}</div>
          {flags_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_policy_badge(policy: dict) -> None:
    action = str(policy.get("action", "answer"))
    tone = POLICY_TONES.get(action, POLICY_TONES["safe_template"])
    reason = policy.get("reason", "")
    st.markdown(
        f"""
        <div style="{_card_style(tone['bg'], tone['border'], tone['text'])}">
          <div style="font-size:13px;font-weight:800;margin-bottom:6px;">POLICY ACTION</div>
          <div style="font-size:28px;font-weight:900;line-height:1.2;">{escape(action)}</div>
          <div style="margin-top:9px;line-height:1.55;">{escape(str(reason))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_answer_panel(answer: dict) -> None:
    mode = answer.get("mode", "safe")
    text = answer.get("text", "")
    st.markdown(
        f"""
        <div style="background:#ffffff;border:1px solid #d8e0ea;border-radius:8px;padding:15px;margin-bottom:12px;">
          <div style="color:#627083;font-weight:800;font-size:13px;margin-bottom:8px;">ANSWER OUTPUT · {escape(str(mode))}</div>
          <div style="font-size:16px;line-height:1.65;color:#162033;">{escape(str(text))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_evidence_cards(evidence: list[dict]) -> None:
    if not evidence:
        st.info("当前 trace 没有可展示的检索证据。")
        return

    for item in evidence:
        status = str(item.get("status", "trusted"))
        tone = EVIDENCE_TONES.get(status, EVIDENCE_TONES["suspicious"])
        st.markdown(
            f"""
            <div style="{_card_style(tone['bg'], tone['border'], tone['text'])}">
              <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
                <strong>{escape(str(item.get('title', 'Evidence')))}</strong>
                <span style="font-weight:900;">{escape(tone['label'])}</span>
              </div>
              <div style="margin-top:8px;line-height:1.58;">{escape(str(item.get('snippet', '')))}</div>
              <div style="margin-top:10px;font-size:12px;">
                source={escape(str(item.get('source', 'local demo')))}
                &nbsp; page={escape(str(item.get('page', '-')))}
                &nbsp; hash={escape(str(item.get('hash', 'demo_hash')))}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_pipeline_summary(trace: dict) -> None:
    steps = [
        ("Query Scan", trace.get("query_scan", {}).get("status", "neutral")),
        ("Retrieval", trace.get("retrieval", {}).get("status", "neutral")),
        ("M-EPI", trace.get("mepi", {}).get("status", "neutral")),
        ("Consistency", trace.get("consistency", {}).get("status", "neutral")),
        ("Policy", trace.get("policy", {}).get("action", "answer")),
        ("Audit", "valid" if trace.get("audit", {}).get("chain_valid") else "pending"),
    ]
    cols = st.columns(len(steps))
    for col, (label, status) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div style="background:#ffffff;border:1px solid #d8e0ea;border-radius:8px;padding:12px;min-height:82px;">
                  <div style="color:#627083;font-size:12px;font-weight:800;">{escape(label)}</div>
                  <div style="margin-top:8px;color:#162033;font-weight:900;overflow-wrap:anywhere;">{escape(str(status))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
