#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Metric rendering helpers for the Streamlit frontend."""

from __future__ import annotations

import streamlit as st


BENCHMARK_METRICS = {
    "pass_rate": "93.3%",
    "behavior_pass_rate": "94.3%",
    "benign_pass_rate": "100%",
    "poison_block_rate": "100%",
    "canary_leak_count": "0",
    "poison_citation_count": "0",
    "audit_coverage": "100%",
}

COMPARISON_ROWS = [
    {
        "setting": "Naive RAG",
        "pass_rate": "10%",
        "attack_block": "0%",
        "poison_block": "0%",
        "canary_leak_count": 97,
        "poison_citation_count": 255,
    },
    {
        "setting": "SafePLC-RAGShield",
        "pass_rate": "93.3%",
        "attack_block": "90.44%",
        "poison_block": "100%",
        "canary_leak_count": 0,
        "poison_citation_count": 0,
    },
]


def render_metric_strip(metrics: dict) -> None:
    items = [
        ("risk_level", "风险等级"),
        ("evidence_count", "证据数"),
        ("poison_detected", "投毒命中"),
        ("audit_recorded", "审计记录"),
    ]
    cols = st.columns(len(items))
    for col, (key, label) in zip(cols, items):
        value = metrics.get(key, "-")
        col.metric(label, value)


def render_benchmark_board() -> None:
    st.markdown("#### 完整链路结果")
    cols = st.columns(4)
    metric_items = list(BENCHMARK_METRICS.items())
    for index, (key, value) in enumerate(metric_items):
        cols[index % 4].metric(key, value)

    st.markdown("#### Naive RAG vs SafePLC-RAGShield")
    st.table(COMPARISON_ROWS)

    st.markdown("#### 关键对比")
    c1, c2 = st.columns(2)
    with c1:
        st.progress(0.10, text="Naive RAG pass_rate 10%")
        st.progress(0.933, text="SafePLC-RAGShield pass_rate 93.3%")
    with c2:
        st.progress(0.0, text="Naive poison_block 0%")
        st.progress(1.0, text="SafePLC-RAGShield poison_block 100%")

    st.caption(
        "展示口径：gateway=off，oracle_rules=false。Naive RAG 作为无安全链路基线；"
        "SafePLC-RAGShield 表示可信审查链路开启后的完整系统结果。"
    )
