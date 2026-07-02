#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SafePLC-RAGShield Streamlit frontend entrypoint."""

from __future__ import annotations

import streamlit as st

from core.demo_backend import load_demo_cases, run_demo_pipeline
from frontend.render_audit import render_audit_center
from frontend.render_benchmark import render_benchmark_analysis
from frontend.render_style import apply_global_style
from frontend.render_workspace import render_workspace


st.set_page_config(
    page_title="SafePLC-RAGShield 工业可信 RAG 安全工作台 V2",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_session_state() -> None:
    demo_cases = load_demo_cases()
    default_query = demo_cases[0]["query"] if demo_cases else ""
    defaults = {
        "current_query": default_query,
        "query_input": default_query,
        "current_trace": None,
        "history_queries": [],
        "history_runs": [],
        "selected_demo": demo_cases[0]["name"] if demo_cases else "",
        "backend_mode": "demo",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    if st.session_state.current_trace is None and default_query:
        st.session_state.current_trace = run_demo_pipeline(default_query)


def _render_sidebar() -> None:
    st.sidebar.title("SafePLC-RAGShield")
    st.sidebar.caption("侧边栏仅展示状态和最近历史；主输入区在安全工作台顶部。")
    st.sidebar.divider()
    st.sidebar.metric("最近运行数", len(st.session_state.history_runs))
    st.sidebar.metric("当前后端模式", st.session_state.get("backend_mode", "demo"))

    if st.session_state.history_runs:
        st.sidebar.markdown("#### 最近运行历史")
        for item in reversed(st.session_state.history_runs[-10:]):
            action = item.get("action", "-")
            query = item.get("query", "")
            st.sidebar.caption(f"{action} · {query[:42]}")
    else:
        st.sidebar.info("还没有运行历史。")


def main() -> None:
    apply_global_style()
    _init_session_state()
    _render_sidebar()

    st.markdown(
        """
        <div class="safeplc-hero">
          <div class="safeplc-kicker">Industrial Trusted RAG Security Workbench</div>
          <h1>SafePLC-RAGShield 工业可信 RAG 安全工作台 V2</h1>
          <p>
            自由输入 PLC 工业知识问题或安全测试样例，系统将展示 Query Scan、Chroma/BGE Retrieval、
            Evidence Scan、M-EPI、Consistency Check、Risk Policy 与 SM3 Hash-chain Audit 的完整可信链路。
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_workspace, tab_benchmark, tab_audit = st.tabs(["安全工作台", "Benchmark 与分析", "国密审计中心"])
    with tab_workspace:
        render_workspace()
    with tab_benchmark:
        render_benchmark_analysis()
    with tab_audit:
        render_audit_center(st.session_state.current_trace, st.session_state.history_runs)


if __name__ == "__main__":
    main()
