#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
AGENT_V2_SCRIPT = BASE_DIR / "ask_s7_agent_v2.py"


st.set_page_config(
    page_title="S7 多模态 RAG Agent v2",
    layout="wide",
)

st.title("S7-1500 / ET 200MP 多模态 RAG Agent v2")
st.caption("多轮澄清 / 自动追问 / Safety Guard v1 继承 / Agent v1 推理规划")

with st.sidebar:
    st.header("样例问题")
    samples = [
        "CPU 1517-3 PN 的 PROFINET 接口 X1 X2",
        "某个模块的电源电压允许范围是多少",
        "PS 60W 24/48/60DC HF 电源电压允许范围是多少",
        "PROFINET 环网如何连接 HMI 设备",
        "能不能带电接 24V 电源端子",
        "EMC 要求是什么",
    ]
    selected = st.radio("选择样例", samples, index=0)
    st.markdown("---")
    st.info("当问题缺少型号或订货号时，Agent v2 会先追问，不会直接误查其它模块。")

if "question" not in st.session_state:
    st.session_state.question = selected

if st.button("使用左侧样例"):
    st.session_state.question = selected

question = st.text_area(
    "问题",
    value=st.session_state.question,
    height=90,
    placeholder="例如：某个模块的电源电压允许范围是多少",
)

context = st.text_input(
    "补充上下文，可选",
    value="",
    placeholder="例如：PS 60W 24/48/60VDC HF / CPU 1517-3 PN / 6ES7...",
)

force = st.checkbox("强制执行检索（不推荐）", value=False)

col1, col2 = st.columns([1, 1])
run_clicked = col1.button("运行 Agent v2", type="primary")
clear_clicked = col2.button("清空")

if clear_clicked:
    st.session_state.question = ""
    st.rerun()

if run_clicked:
    q = question.strip()
    c = context.strip()

    if not q:
        st.warning("请输入问题。")
        st.stop()

    cmd = [sys.executable, str(AGENT_V2_SCRIPT), q]
    if c:
        cmd.extend(["--context", c])
    if force:
        cmd.append("--force")

    with st.spinner("Agent v2 正在分析问题并执行..."):
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )

    if proc.returncode != 0:
        st.error(f"运行失败，返回码：{proc.returncode}")
        if proc.stderr:
            st.code(proc.stderr, language="text")

    output = proc.stdout or ""

    st.subheader("Agent v2 输出")
    st.code(output, language="text")

    if "【是否需要澄清】是" in output:
        st.warning("该问题需要补充上下文。请在上方填写型号、订货号或模块名称后再次运行。")

    if "【安全等级】HIGH_RISK" in output:
        st.error("该问题被判定为高风险，系统不会提供危险操作步骤。")

    if "【是否继续执行】是" in output:
        st.success("Agent v2 已继续执行。")
