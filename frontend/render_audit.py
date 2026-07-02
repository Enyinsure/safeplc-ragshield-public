#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""National-cryptography audit center rendering."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .render_common import dataframe_from_records, html_card


def _audit_summary(trace: dict | None) -> dict:
    trace = trace or {}
    audit = trace.get("audit", {})
    policy = trace.get("policy", {})
    return {
        "chain_valid": audit.get("chain_valid", False),
        "event_count": audit.get("event_count", 0),
        "last_event_id": audit.get("event_id", ""),
        "prev_hash": audit.get("prev_hash", ""),
        "curr_hash": audit.get("curr_hash", ""),
        "last_action": policy.get("action", "-"),
        "last_risk_level": policy.get("risk_level", "-"),
    }


def render_audit_center(trace: dict | None, history_runs: list[dict]) -> None:
    summary = _audit_summary(trace)
    left, right = st.columns([1, 1])
    with left:
        st.markdown("### SM3 哈希链状态")
        html_card(
            "SM3 哈希链状态：已实现",
            f"<div style='font-size:28px;font-weight:950;'>chain_valid = {summary['chain_valid']}</div>"
            f"<div>event_count = {summary['event_count']}</div>"
            f"<div>last_event_id = {summary['last_event_id']}</div>"
            f"<div>last_action = {summary['last_action']}</div>"
            f"<div>last_risk_level = {summary['last_risk_level']}</div>",
            tone="trusted" if summary["chain_valid"] else "disabled",
        )
        st.code(f"prev_hash = {summary['prev_hash']}\ncurr_hash = {summary['curr_hash']}")

    with right:
        st.markdown("### 国密能力状态表")
        capabilities = [
            {
                "模块": "SM3 哈希链审计",
                "状态": "已实现",
                "作用": "对 query、evidence、policy、answer 等关键字段生成摘要，并通过 prev_hash / curr_hash 串联，支持篡改发现。",
            },
            {
                "模块": "SM2 签名验签",
                "状态": "已接入代码接口，竞赛部署可增强为合规 KMS",
                "作用": "对审计链根哈希、benchmark 结果和策略版本进行签名验真，支持来源认证。",
            },
            {
                "模块": "SM4 日志封存",
                "状态": "已接入代码接口，竞赛部署可增强密钥轮换",
                "作用": "对审计日志、风险样本和评测报告进行本地加密封存。",
            },
            {
                "模块": "国密 TLS/TLCP",
                "状态": "部署增强路径",
                "作用": "用于前端终端与后端服务之间的国密安全传输。",
            },
        ]
        st.dataframe(capabilities, use_container_width=True, hide_index=True)

    st.markdown("### 审计事件时间线")
    records = (trace or {}).get("audit", {}).get("records", [])
    if records:
        st.dataframe(dataframe_from_records(records), use_container_width=True, hide_index=True)
    else:
        st.info("当前没有审计事件。")

    st.markdown("### 最近审计日志表")
    if history_runs:
        st.dataframe(pd.DataFrame(history_runs), use_container_width=True, hide_index=True)
    else:
        st.info("运行安全工作台后，这里会显示最近 10 次审计摘要。")

    st.markdown("### 审计说明")
    st.warning(
        "本页面仅展示审计摘要，不展示 token、私钥、服务器路径、模型权重路径、原始工业手册或敏感配置。"
    )
