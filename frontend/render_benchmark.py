#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Benchmark and analysis page."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data" / "benchmark_summary.json"


def _load_summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def render_benchmark_analysis() -> None:
    summary = _load_summary()
    main = summary["main_result"]
    st.markdown("### 主实验结果")
    keys = [
        "case_count",
        "pass_rate",
        "behavior_pass_rate",
        "attack_block_rate",
        "benign_pass_rate",
        "poison_block_rate",
        "canary_leak_count",
        "poison_citation_count",
        "audit_coverage",
        "llm_called_count",
        "fallback_case_count",
        "chroma_case_count",
    ]
    cols = st.columns(4)
    for index, key in enumerate(keys):
        cols[index % 4].metric(key, main[key])

    st.markdown("### Baseline 对比")
    baseline_df = _df(summary["baseline_comparison"])
    st.dataframe(baseline_df, use_container_width=True, hide_index=True)
    st.bar_chart(baseline_df.set_index("setting")[["pass_rate"]])
    st.bar_chart(baseline_df.set_index("setting")[["attack_block", "poison_block"]])
    st.bar_chart(baseline_df.set_index("setting")[["canary_leak_count", "poison_citation_count"]])

    st.markdown("### 分类分析")
    dimension = st.selectbox("分析维度", ["攻击类型", "OWASP LLM Top 10", "难度等级", "数据划分", "模块消融"])
    key_map = {
        "攻击类型": "attack_family",
        "OWASP LLM Top 10": "owasp",
        "难度等级": "difficulty",
        "数据划分": "split",
        "模块消融": "ablation",
    }
    data_key = key_map[dimension]
    df = _df(summary[data_key])
    st.dataframe(df, use_container_width=True, hide_index=True)
    index_col = df.columns[0]
    value_col = "pass_rate"
    st.bar_chart(df.set_index(index_col)[[value_col]])

    st.markdown("### Benchmark 解释")
    st.info(
        "Naive RAG 在良性样本上可以回答，但面对证据投毒和间接提示注入时缺乏证据审查能力。"
        "SafePLC-RAGShield 通过 Query Scan、Evidence Scan、M-EPI、Risk Policy 和 SM3 Hash-chain Audit "
        "形成可信链路，使污染证据不进入模型上下文，并实现 0 次 canary 泄露与 0 次污染证据引用。"
    )
