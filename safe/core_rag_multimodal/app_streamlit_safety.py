import re
import subprocess
import time
from pathlib import Path

import streamlit as st


HOME = Path.home()

APP = HOME / "s7_multimodal_v1/ask_s7_multimodal_final_safety.py"
IMG_DIR = HOME / "s7_multimodal_v1/images/visual_candidate_pages"

SAMPLES = [
    "CPU 1517-3 PN 的 PROFINET 接口 X1 X2",
    "PS 60W 24/48/60DC HF 电源电压允许范围是多少",
    "PROFINET 环网如何连接 HMI 设备",
    "24 V DC 电源电压端子怎么接线",
    "CPU 1517-3 PN/DP 有哪些接口",
    "PROFINET 环网中设备数量有什么限制",
]


def run_rag(question: str):
    start = time.time()
    r = subprocess.run(
        ["python", str(APP), question],
        text=True,
        capture_output=True,
        timeout=240,
    )
    elapsed = time.time() - start

    out = r.stdout.strip()
    err = r.stderr.strip()

    if r.returncode != 0:
        raise RuntimeError((out + "\n" + err).strip())

    if err:
        out += "\n\n[stderr]\n" + err

    return out, elapsed


def get_route(output: str):
    for line in output.splitlines():
        if line.startswith("路由："):
            return line.replace("路由：", "").strip()
    return "unknown"


def split_sections(output: str):
    titles = {
        "答案",
        "依据",
        "关键证据",
        "图文补充",
        "补充图文证据",
        "文本回答",
    }

    sections = {}
    current = "头部信息"
    buf = []

    for line in output.splitlines():
        s = line.strip()

        if s in titles:
            if buf:
                sections[current] = "\n".join(buf).strip()
            current = s
            buf = []
            continue

        if s and set(s) <= {"=", "-"}:
            continue

        buf.append(line)

    if buf:
        sections[current] = "\n".join(buf).strip()

    return sections


def parse_page_from_text(text: str):
    m = re.search(r"页码[:：]\s*(\d+)", text)
    if m:
        return int(m.group(1))

    m = re.search(r"page[=：:]\s*(\d+)", text)
    if m:
        return int(m.group(1))

    return None


def image_path_for_page(page: int):
    if page is None:
        return None

    candidates = [
        IMG_DIR / f"page_{page:04d}.jpg",
        IMG_DIR / f"page_{page}.jpg",
        IMG_DIR / f"page_{page:04d}.png",
        IMG_DIR / f"page_{page}.png",
    ]

    for p in candidates:
        if p.exists():
            return p

    return None


st.set_page_config(
    page_title="S7 多模态 RAG",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ S7-1500 / ET 200MP 中文手册多模态 RAG")
st.caption("文本 RAG + 表格 RAG + 图文 RAG · Streamlit 前端 v3 · 支持证据图片显示")

with st.sidebar:
    st.header("示例问题")
    sample = st.radio("选择样例", SAMPLES)
    st.divider()
    st.write("最终入口：")
    st.code(str(APP), language="text")
    st.write("图像目录：")
    st.code(str(IMG_DIR), language="text")

question = st.text_area(
    "请输入问题",
    value=sample,
    height=90,
)

if st.button("开始检索", type="primary"):
    q = question.strip()

    if not q:
        st.warning("请输入问题。")
    else:
        with st.spinner("正在检索..."):
            try:
                output, elapsed = run_rag(q)
                route = get_route(output)
                sections = split_sections(output)

                st.success("检索完成")

                c1, c2, c3 = st.columns(3)
                c1.metric("路由", route)
                c2.metric("耗时", f"{elapsed:.2f} s")
                c3.metric("入口", "final")

                left, right = st.columns([1.25, 1])

                with left:
                    if "答案" in sections:
                        st.subheader("答案")
                        st.markdown(sections["答案"])

                    if "依据" in sections:
                        st.subheader("依据")
                        st.code(sections["依据"], language="text")

                    if "关键证据" in sections:
                        st.subheader("关键证据")
                        st.code(sections["关键证据"], language="text")

                    if "图文补充" in sections:
                        st.subheader("图文补充")
                        st.code(sections["图文补充"], language="text")

                    if "补充图文证据" in sections:
                        st.subheader("补充图文证据")
                        st.code(sections["补充图文证据"], language="text")

                with right:
                    st.subheader("图文证据图片")

                    page = None
                    if "依据" in sections:
                        page = parse_page_from_text(sections["依据"])

                    img = image_path_for_page(page)

                    if route == "figure" and img:
                        st.image(str(img), caption=f"图文证据页：page {page}", use_container_width=True)
                        st.code(str(img), language="text")
                    elif route == "figure":
                        st.info("当前问题为 figure 路由，但未找到对应页面图片。")
                    else:
                        st.info("当前为 table / mixed 路由，主证据以文本或表格为主。")

                with st.expander("查看原始完整输出"):
                    st.code(output, language="text")

            except Exception as e:
                st.error("运行失败")
                st.code(str(e), language="text")
