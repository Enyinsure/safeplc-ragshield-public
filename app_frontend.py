#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Streamlit demo frontend for SafePLC-RAGShield."""

from __future__ import annotations

import streamlit as st

from core.demo_backend import DEMO_CASES, get_demo_trace
from frontend.render_audit import render_audit_log
from frontend.render_cards import (
    render_answer_panel,
    render_evidence_cards,
    render_pipeline_summary,
    render_policy_badge,
    render_trace_step,
)
from frontend.render_metrics import render_benchmark_board, render_metric_strip


st.set_page_config(
    page_title="SafePLC-RAGShield 工业可信 RAG 安全演示平台",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_page_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #d8e0ea;
            border-radius: 8px;
            padding: 14px 14px 10px;
        }
        div[data-testid="stMetric"] label {
            color: #627083;
        }
        .safeplc-header {
            border: 1px solid #d8e0ea;
            border-radius: 8px;
            padding: 18px 20px;
            background: #ffffff;
            margin-bottom: 16px;
        }
        .safeplc-kicker {
            color: #627083;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .safeplc-header h1 {
            margin: 0;
            font-size: 28px;
            line-height: 1.25;
        }
        .safeplc-subtitle {
            color: #4d5b6c;
            margin-top: 8px;
            margin-bottom: 0;
            line-height: 1.55;
        }
        .safeplc-section-note {
            color: #627083;
            font-size: 14px;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str]:
    st.sidebar.title("演示样例")
    case_name = st.sidebar.radio(
        "选择安全场景",
        list(DEMO_CASES.keys()),
        index=0,
        help="四个样例覆盖正常回答、澄清、危险拒答和投毒阻断。",
    )
    default_query = DEMO_CASES[case_name]["query"]
    query = st.sidebar.text_area("演示查询", value=default_query, height=120)
    st.sidebar.divider()
    st.sidebar.caption("前端统一使用 trace dict 渲染，便于后续接入真实 RAG 后端。")
    st.sidebar.caption("不包含模型权重、向量库、原始工业手册、服务器路径、token 或私钥。")
    return case_name, query


def render_realtime_tab(trace: dict) -> None:
    left, right = st.columns([1.08, 0.92])
    with left:
        st.subheader("请求链路状态")
        render_trace_step("用户查询", trace["query"], tone="neutral")
        render_trace_step("Query Scan", trace["query_scan"], tone=trace["query_scan"].get("status", "neutral"))
        render_trace_step("Retrieval", trace["retrieval"], tone=trace["retrieval"].get("status", "neutral"))
        render_trace_step("M-EPI", trace["mepi"], tone=trace["mepi"].get("status", "neutral"))
        render_trace_step("Consistency", trace["consistency"], tone=trace["consistency"].get("status", "neutral"))

    with right:
        st.subheader("策略动作")
        render_policy_badge(trace["policy"])
        render_answer_panel(trace["answer"])
        st.markdown("#### 核心指标")
        render_metric_strip(trace["metrics"])


def render_evidence_tab(trace: dict) -> None:
    st.subheader("证据链展示")
    st.markdown(
        '<p class="safeplc-section-note">证据卡片按状态着色：trusted 为绿色，suspicious 为黄色，blocked_poison 为红色。</p>',
        unsafe_allow_html=True,
    )
    render_pipeline_summary(trace)
    render_evidence_cards(trace["evidence"])


def render_benchmark_tab() -> None:
    st.subheader("Benchmark 看板")
    render_benchmark_board()


def render_audit_tab(trace: dict) -> None:
    st.subheader("国密审计日志")
    render_audit_log(trace["audit"])


def main() -> None:
    inject_page_style()
    case_name, query = render_sidebar()
    trace = get_demo_trace(case_name, query=query)

    st.markdown(
        """
        <div class="safeplc-header">
          <div class="safeplc-kicker">Industrial Trusted RAG Security Chain</div>
          <h1>SafePLC-RAGShield 工业可信 RAG 安全演示平台</h1>
          <p class="safeplc-subtitle">
            面向工业 PLC 知识问答的可信 RAG 安全链路演示：输入扫描、检索证据审查、
            M-EPI 多模态证据污染评估、一致性校验、风险策略和审计链追踪。
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_realtime, tab_evidence, tab_benchmark, tab_audit = st.tabs(
        ["实时安全问答", "证据链展示", "Benchmark 看板", "国密审计日志"]
    )
    with tab_realtime:
        render_realtime_tab(trace)
    with tab_evidence:
        render_evidence_tab(trace)
    with tab_benchmark:
        render_benchmark_tab()
    with tab_audit:
        render_audit_tab(trace)


if __name__ == "__main__":
    main()
