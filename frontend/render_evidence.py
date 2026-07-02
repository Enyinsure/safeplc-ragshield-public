#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evidence rendering for the SafePLC Streamlit workbench."""

from __future__ import annotations

from html import escape

import streamlit as st

from .render_common import dataframe_from_records, status_tone


def render_evidence_cards(evidence_list: list[dict]) -> None:
    if not evidence_list:
        st.info("当前模块未检索证据，或检索模块已关闭。")
        return

    for item in evidence_list:
        status = str(item.get("status", "trusted"))
        labels = item.get("risk_labels") or []
        used = "Yes" if item.get("used_in_context") else "No"
        title = f"{item.get('id', '-')}: {item.get('title', 'Evidence')}"
        summary = (
            f"<div><b>状态：</b>{escape(status)}</div>"
            f"<div><b>来源：</b>{escape(str(item.get('source', 'local demo')))}</div>"
            f"<div><b>页码 / image_id：</b>{escape(str(item.get('page', '-')))} / {escape(str(item.get('image_id', '-')))}</div>"
            f"<div><b>检索分数：</b>{escape(str(item.get('retrieval_score', '-')))}</div>"
            f"<div><b>进入模型上下文：</b>{used}</div>"
            f"<div><b>风险标签：</b>{escape(', '.join(labels) if labels else 'none')}</div>"
            f"<div><b>证据哈希：</b>{escape(str(item.get('hash', '')))}</div>"
        )
        st.markdown(
            f"""
            <div class="safeplc-card tone-{status_tone(status)}">
              <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
                <div class="safeplc-title">{escape(title)}</div>
                <span class="safeplc-badge">{escape(status)}</span>
              </div>
              {summary}
              <div style="margin-top:9px;line-height:1.58;">{escape(str(item.get('text', '')))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"展开完整证据与检测详情 · {item.get('id', '-')}"):
            st.write("证据文本")
            st.code(str(item.get("text", "")))
            st.write("风险原因")
            st.write(item.get("risk_reason", ""))
            st.json(item)


def render_evidence_table(evidence_list: list[dict]) -> None:
    if not evidence_list:
        st.info("没有证据表格可展示。")
        return
    st.dataframe(dataframe_from_records(evidence_list), use_container_width=True, hide_index=True)
