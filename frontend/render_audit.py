#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit rendering helpers for the Streamlit frontend."""

from __future__ import annotations

from html import escape

import streamlit as st


def _info_box(title: str, value: str, detail: str, color: str = "#244d91") -> None:
    st.markdown(
        f"""
        <div style="background:#ffffff;border:1px solid #d8e0ea;border-radius:8px;padding:14px;margin-bottom:10px;">
          <div style="color:#627083;font-size:12px;font-weight:800;">{escape(title)}</div>
          <div style="color:{color};font-size:18px;font-weight:900;margin-top:6px;">{escape(value)}</div>
          <div style="color:#4d5b6c;line-height:1.55;margin-top:7px;">{escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_audit_log(audit: dict) -> None:
    left, right = st.columns([1.1, 0.9])

    with left:
        st.markdown("#### SM3 哈希链")
        _info_box(
            "SM3 哈希链状态",
            str(audit.get("sm3_status", "已实现")),
            "对 query、evidence、policy、answer 等关键字段生成摘要，并通过 prev_hash / curr_hash 串联。",
            color="#005f59",
        )
        st.code(f"prev_hash = {audit.get('prev_hash', '')}\ncurr_hash = {audit.get('curr_hash', '')}")
        st.metric("chain_valid", str(audit.get("chain_valid", False)))

    with right:
        st.markdown("#### 竞赛增强接口")
        _info_box(
            "SM2 签名接口状态",
            str(audit.get("sm2_status", "竞赛增强接口")),
            "前端展示签名/验签接口位置；正式部署可接入合规国密密钥管理与签名服务。",
            color="#7a4b00",
        )
        _info_box(
            "SM4 日志封存接口状态",
            str(audit.get("sm4_status", "竞赛增强接口")),
            "前端展示日志封存/解封流程；正式部署可接入本地加密封存和密钥轮换策略。",
            color="#7a4b00",
        )
        _info_box(
            "国密 TLS/TLCP 部署增强路径",
            str(audit.get("tlcp_status", "部署增强路径")),
            "建议在网关或内网服务入口启用国密 TLS/TLCP，用于链路传输保护。",
            color="#4b3a85",
        )

    st.caption("说明：该演示页不展示 token、私钥、服务器路径、模型权重、向量库或原始工业手册。")
