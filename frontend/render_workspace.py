#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Security workbench rendering."""

from __future__ import annotations

import streamlit as st

from core.demo_backend import load_demo_cases
from core.pipeline_adapter import run_pipeline
from .render_common import (
    dataframe_from_records,
    render_answer,
    render_chain_card,
    render_metric_row,
    render_policy_action,
)
from .render_evidence import render_evidence_cards, render_evidence_table


def _config_from_state() -> dict:
    return {
        "backend_mode": st.session_state.get("backend_mode", "demo"),
        "top_k": st.session_state.get("top_k", 5),
        "enable_query_scan": st.session_state.get("enable_query_scan", True),
        "enable_retrieval": st.session_state.get("enable_retrieval", True),
        "enable_evidence_scan": st.session_state.get("enable_evidence_scan", True),
        "enable_mepi": st.session_state.get("enable_mepi", True),
        "enable_consistency": st.session_state.get("enable_consistency", True),
        "enable_audit": st.session_state.get("enable_audit", True),
        "review_mode": st.session_state.get("review_mode", "trusted"),
        "generator": st.session_state.get("generator", "qwen"),
        "poison_mode": st.session_state.get("poison_mode", "overlay"),
    }


def _save_run(trace: dict) -> None:
    query = trace.get("query", st.session_state.get("query_input", ""))
    st.session_state.current_trace = trace
    st.session_state.current_query = query
    st.session_state.history_queries.append(query)
    summary = {
        "run_id": trace.get("run_id"),
        "query": trace.get("query"),
        "action": trace.get("policy", {}).get("action"),
        "risk_level": trace.get("policy", {}).get("risk_level"),
        "audit_required": trace.get("policy", {}).get("audit_required"),
        "curr_hash": trace.get("audit", {}).get("curr_hash"),
        "chain_valid": trace.get("audit", {}).get("chain_valid"),
        "timestamp": trace.get("timestamp"),
    }
    st.session_state.history_runs.append(summary)
    st.session_state.history_runs = st.session_state.history_runs[-10:]


def _set_query_input(query: str) -> None:
    st.session_state.query_input = query


def render_query_input() -> None:
    demo_cases = load_demo_cases()
    demo_map = {case["name"]: case for case in demo_cases}

    st.markdown(
        """
        <div class="safeplc-panel">
          <div class="safeplc-kicker">Security Workbench</div>
          <h2 style="margin:0;color:#111827;">工业可信 RAG 安全工作台</h2>
          <p class="safeplc-muted">
            输入 PLC 工业知识问题或攻击样例，系统将展示查询扫描、证据检索、证据安全检测、
            M-EPI、多模态一致性、风险策略与国密审计链路。
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    load_col, button_col = st.columns([3, 1])
    with load_col:
        selected = st.selectbox("加载 demo 样例", list(demo_map.keys()), key="selected_demo")
    with button_col:
        st.write("")
        st.write("")
        st.button(
            "加载样例到输入框",
            use_container_width=True,
            on_click=_set_query_input,
            args=(demo_map[selected]["query"],),
        )

    st.text_area(
        "请输入工业知识问题或安全测试样例",
        key="query_input",
        height=120,
        placeholder="例如：S7-1500 CPU 的 ERROR 指示灯亮起时，应该如何进行安全排查？",
    )

    with st.expander("高级参数", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.selectbox("backend_mode", ["demo", "real"], key="backend_mode")
            st.slider("top_k", 1, 10, key="top_k", value=st.session_state.get("top_k", 5))
        with c2:
            st.checkbox("enable_query_scan", key="enable_query_scan", value=st.session_state.get("enable_query_scan", True))
            st.checkbox("enable_retrieval", key="enable_retrieval", value=st.session_state.get("enable_retrieval", True))
        with c3:
            st.checkbox("enable_evidence_scan", key="enable_evidence_scan", value=st.session_state.get("enable_evidence_scan", True))
            st.checkbox("enable_mepi", key="enable_mepi", value=st.session_state.get("enable_mepi", True))
        with c4:
            st.checkbox("enable_consistency", key="enable_consistency", value=st.session_state.get("enable_consistency", True))
            st.checkbox("enable_audit", key="enable_audit", value=st.session_state.get("enable_audit", True))
        c5, c6, c7 = st.columns(3)
        with c5:
            st.selectbox("review_mode", ["trusted", "naive", "qwen"], key="review_mode")
        with c6:
            st.selectbox("generator", ["qwen", "none"], key="generator")
        with c7:
            st.selectbox("poison_mode", ["overlay", "off"], key="poison_mode")

    run_col, retrieve_col, clear_col = st.columns([1, 1, 1])
    with run_col:
        if st.button("运行完整链路", type="primary", use_container_width=True):
            trace = run_pipeline(st.session_state.get("query_input", ""), _config_from_state())
            _save_run(trace)
    with retrieve_col:
        if st.button("仅检索证据", use_container_width=True):
            config = _config_from_state()
            config.update({"enable_query_scan": False, "enable_evidence_scan": False, "enable_mepi": False, "enable_consistency": False})
            trace = run_pipeline(st.session_state.get("query_input", ""), config)
            trace["logs"].append("[Frontend] retrieval-only mode requested")
            _save_run(trace)
    with clear_col:
        st.button("清空输入", use_container_width=True, on_click=_set_query_input, args=("",))


def render_chain_status(trace: dict) -> None:
    st.markdown("#### 请求链路状态")
    render_chain_card("Query Scan", trace.get("query_scan", {}))
    render_chain_card("Chroma/BGE Retrieval", trace.get("retrieval", {}))
    render_chain_card("Evidence Scan", trace.get("evidence_scan", {}))
    render_chain_card("M-EPI", trace.get("mepi", {}))
    render_chain_card("Consistency Check", trace.get("consistency", {}))
    render_chain_card("Risk Policy", trace.get("policy", {}), status_key="action")
    audit_data = trace.get("audit", {})
    render_chain_card(
        "SM3 Hash-chain Audit",
        {
            "status": "trusted" if audit_data.get("chain_valid") else "disabled",
            "labels": [audit_data.get("algorithm", "SM3")],
            "reason": f"curr_hash={audit_data.get('curr_hash', '')}",
            "latency_ms": "-",
        },
    )


def render_detail_tabs(trace: dict) -> None:
    evidence_tab, policy_tab, audit_tab, raw_tab, log_tab = st.tabs(["证据详情", "策略依据", "审计日志", "原始 Trace JSON", "运行日志"])
    with evidence_tab:
        render_evidence_table(trace.get("evidence", []))
    with policy_tab:
        st.write(trace.get("policy", {}).get("reason", ""))
        for item in trace.get("policy_basis", []):
            st.markdown(f"- {item}")
    with audit_tab:
        records = trace.get("audit", {}).get("records", [])
        st.dataframe(dataframe_from_records(records), use_container_width=True, hide_index=True)
    with raw_tab:
        st.json(trace)
    with log_tab:
        for line in trace.get("logs", []):
            st.code(line)


def render_workspace() -> None:
    render_query_input()
    trace = st.session_state.get("current_trace")
    if not trace:
        st.info("请输入问题并点击“运行完整链路”。")
        return
    if trace.get("backend_warning"):
        st.warning(trace["backend_warning"])

    left_col, right_col = st.columns([1.35, 1])
    with left_col:
        render_chain_status(trace)
        st.markdown("#### 证据卡片")
        render_evidence_cards(trace.get("evidence", []))
    with right_col:
        render_policy_action(trace.get("policy", {}))
        render_answer(trace.get("answer", {}))
        st.markdown("#### 核心指标")
        render_metric_row(trace.get("metrics", {}))

    render_detail_tabs(trace)
