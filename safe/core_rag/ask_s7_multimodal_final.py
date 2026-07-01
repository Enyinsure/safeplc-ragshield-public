import os
os.environ.setdefault("TQDM_DISABLE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import re
import sys
import subprocess
from pathlib import Path

import torch
import chromadb
from sentence_transformers import SentenceTransformer

HOME = Path.home()

ASK_TABLE = HOME / "ask_s7_tables_priority_stable.py"
ASK_TEXT = HOME / "ask_s7_stable.py"

FIG_DB_PATH = str(HOME / "s7_multimodal_v1/index/chroma_figures_v1")
FIG_COLLECTION = "s7_figures_v1"
MODEL_BASE_DIR = HOME / ".cache/modelscope/BAAI"


FIGURE_TERMS = [
    "图", "图示", "图片", "硬件图", "接线图", "接线", "端子", "引脚", "针脚",
    "接口", "连接器", "插头", "拓扑", "PROFINET", "PROFIBUS", "RJ45",
    "FastConnect", "X1", "X2", "X3", "P1", "P2", "PN/IE", "24 V DC",
    "电源电压", "负载电源", "系统电源", "HMI", "IRT", "同步域"
]

TABLE_TERMS = [
    "多少", "范围", "允许范围", "额定值", "下限", "上限",
    "参数", "技术数据", "技术规范", "订货号", "型号",
    "尺寸", "宽度", "高度", "深度", "重量", "电流", "电压",
    "功耗", "最大", "最小", "支持", "数量", "规格", "表"
]


def has_any(q, terms):
    ql = q.lower()
    return any(t.lower() in ql for t in terms)


def route(q):
    strong_table_terms = [
        "多少", "范围", "允许范围", "额定值", "下限", "上限",
        "技术规范", "技术数据", "参数", "订货号", "型号",
        "尺寸", "重量", "功耗", "电流", "电压允许", "最大", "最小"
    ]

    strong_figure_terms = [
        "怎么接线", "如何接线", "如何连接", "怎么连接",
        "接线图", "硬件图", "接口图", "拓扑", "环网",
        "端子怎么", "引脚", "针脚", "FastConnect", "RJ45",
        "X1", "X2", "X3", "P1", "P2", "PROFINET 接口"
    ]

    if has_any(q, strong_table_terms):
        return "table"

    if has_any(q, strong_figure_terms):
        return "figure"

    if has_any(q, FIGURE_TERMS):
        return "figure"

    if has_any(q, TABLE_TERMS):
        return "table"

    return "mixed"


def find_embedding_model():
    candidates = list(MODEL_BASE_DIR.glob("bge-small-zh-v1*"))
    if not candidates:
        raise FileNotFoundError(f"找不到 embedding 模型目录：{MODEL_BASE_DIR}")
    return str(candidates[0])


def extract_boost_terms(q: str):
    terms = []

    patterns = [
        r"CPU\s*\d+[A-Z]?(?:-\d+)?\s*(?:PN/DP|PN|DP|T|TF|HF|H|R)?",
        r"PS\s*\d+\s*W?\s*[\d/]*\s*(?:VDC|DC|AC/DC|HF)?",
        r"ET\s*200MP",
        r"PROFINET",
        r"PROFIBUS",
        r"FastConnect",
        r"RJ45",
        r"24\s*V\s*DC",
        r"X\d",
        r"P\dR?",
    ]

    for pat in patterns:
        for m in re.findall(pat, q, flags=re.I):
            t = re.sub(r"\s+", " ", m.strip())
            if t:
                terms.append(t)

    for t in ["接口", "端子", "接线", "引脚", "针脚", "拓扑", "环网", "电源电压"]:
        if t in q:
            terms.append(t)

    out = []
    seen = set()
    for t in terms:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


def rerank_figures(q, docs, metas, dists):
    boost_terms = extract_boost_terms(q)
    ranked = []

    for doc, meta, dist in zip(docs, metas, dists):
        text = doc + "\n" + " ".join(str(v) for v in meta.values())
        text_low = text.lower()

        score = -float(dist)

        for t in boost_terms:
            if t.lower() in text_low:
                score += 2.5

        for t in boost_terms:
            tl = t.lower()
            if tl.startswith("cpu") or tl.startswith("ps"):
                if tl in text_low:
                    score += 5.0

        if any(x in q for x in ["接口", "端子", "接线", "引脚", "针脚", "X1", "X2", "X3"]):
            if meta.get("visual_type") in ["wiring_diagram", "terminal_assignment", "interface_layout"]:
                score += 1.5

        if "CPU 1517-3" in q and "CPU 1517-3" not in text and "1517-3" not in text:
            score -= 4.0

        if "PN/DP" in q and "PN/DP" not in text:
            score -= 2.0

        ranked.append({
            "score": score,
            "distance": float(dist),
            "document": doc,
            "metadata": meta,
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def query_figures(q, n=5):
    model_path = find_embedding_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = SentenceTransformer(model_path, device=device)
    q_emb = model.encode([q], normalize_embeddings=True).tolist()

    client = chromadb.PersistentClient(path=FIG_DB_PATH)
    collection = client.get_collection(FIG_COLLECTION)

    res = collection.query(
        query_embeddings=q_emb,
        n_results=12,
        include=["documents", "metadatas", "distances"],
    )

    ranked = rerank_figures(
        q,
        res["documents"][0],
        res["metadatas"][0],
        res["distances"][0],
    )

    return ranked[:n]


def run_script(script_path, q):
    if not script_path.exists():
        return f"未找到脚本：{script_path}"

    r = subprocess.run(
        ["python", str(script_path), q],
        text=True,
        capture_output=True,
        timeout=180,
    )

    out = r.stdout or ""
    err = r.stderr or ""
    if err.strip():
        out += "\n[stderr]\n" + err

    return out.strip()


def extract_block(text, title):
    """
    从 ask_s7_tables_priority_stable.py 的输出里提取“答案/依据/关键证据”。
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == title:
            start = i
            break

    if start is None:
        return ""

    buf = []
    for line in lines[start + 1:]:
        if line.strip() in ["问题", "答案", "依据", "关键证据"]:
            if buf:
                break
        if set(line.strip()) <= {"-"}:
            continue
        if line.strip():
            buf.append(line.rstrip())

    return "\n".join(buf).strip()


def field_from_doc(doc, name):
    prefix = name + "："
    for line in doc.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def split_semantic_items(text):
    if not text:
        return []
    parts = re.split(r"[；;]\s*|\n+", text)
    return [p.strip(" \t\r\n；;") for p in parts if p.strip(" \t\r\n；;")]


def join_bullets(items, max_items=6):
    items = [x.strip() for x in items if x and x.strip()]
    return "\n".join(f"- {x}" for x in items[:max_items])


def is_network_question(q):
    ql = q.lower()
    return any(t.lower() in ql for t in [
        "profinet", "profibus", "rj45", "fastconnect",
        "x1", "x2", "x3", "p1", "p2", "hmi",
        "环网", "拓扑", "接口", "端口", "工业以太网"
    ])


def is_power_question(q):
    ql = q.lower()
    return any(t.lower() in ql for t in [
        "电源", "电源电压", "24 v", "24v", "负载电源", "系统电源", "供电"
    ])


def is_irrelevant_power_item(item, q):
    if not is_network_question(q) or is_power_question(q):
        return False

    il = item.lower()
    power_terms = ["24 v", "24v", "电源", "供电", "1l+", "2l+", "1m", "2m", "10 a"]
    network_terms = [
        "profinet", "profibus", "rj45", "x1", "x2", "x3",
        "p1", "p2", "hmi", "环网", "拓扑", "接口", "端口",
        "工业以太网", "交换机"
    ]

    return any(t in il for t in power_terms) and not any(t in il for t in network_terms)


def build_focus_terms(q):
    terms = extract_boost_terms(q)

    if is_network_question(q):
        terms += [
            "PROFINET", "PROFIBUS", "RJ45", "FastConnect",
            "X1", "X2", "X3", "P1", "P2", "P1R", "P2R",
            "HMI", "接口", "端口", "环网", "拓扑",
            "工业以太网", "交换机", "CPU"
        ]

    if is_power_question(q):
        terms += [
            "24 V", "24 V DC", "电源", "电源电压",
            "负载电源", "系统电源", "供电", "1L+", "2L+", "1M", "2M"
        ]

    if any(t in q for t in ["接线", "端子", "引脚", "针脚"]):
        terms += ["接线", "端子", "引脚", "针脚", "连接器", "插头"]

    out, seen = [], set()
    for t in terms:
        t = str(t).strip()
        k = t.lower()
        if t and k not in seen:
            seen.add(k)
            out.append(t)
    return out


def filter_field_by_question(text, q, max_items=6, strict=False):
    items = split_semantic_items(text)
    if not items:
        return ""

    focus_low = [t.lower() for t in build_focus_terms(q)]
    filtered, fallback = [], []

    for item in items:
        if is_irrelevant_power_item(item, q):
            continue

        fallback.append(item)
        il = item.lower()
        if any(t in il for t in focus_low):
            filtered.append(item)

    if filtered:
        return join_bullets(filtered, max_items=max_items)

    if strict:
        return ""

    return join_bullets(fallback, max_items=max_items)


def filter_warnings_by_question(text, q, max_items=3):
    items = split_semantic_items(text)
    if not items:
        return ""

    focus_low = [t.lower() for t in build_focus_terms(q)]
    filtered = []

    for item in items:
        if is_irrelevant_power_item(item, q):
            continue

        il = item.lower()

        if any(t in q for t in ["HMI", "环网", "拓扑"]) and any(t in item for t in ["16", "设备数量", "可用性"]):
            filtered.append(item)
            continue

        if any(t in il for t in focus_low):
            filtered.append(item)

    return join_bullets(filtered, max_items=max_items)


def normalize_module_name(name):
    name = re.sub(r"\s+", " ", name.strip())
    name = re.sub(r"(\d)DC\b", r"\1VDC", name, flags=re.I)
    name = re.sub(r"(\d)AC\b", r"\1VAC", name, flags=re.I)
    return name.upper()


def module_name_from_question_or_key(q, key=""):
    m = re.search(
        r"(PS\s*\d+\s*W?\s*[\d/]*\s*(?:VDC|DC|AC/DC|VAC)?\s*(?:HF)?)",
        q,
        flags=re.I,
    )
    if m:
        return normalize_module_name(m.group(1))

    lines = [x.strip() for x in key.splitlines() if x.strip()]
    for i, line in enumerate(lines):
        if "产品类型标志" in line and i + 1 < len(lines):
            return lines[i + 1].strip()

    return ""


def compact_table_key_evidence(key, q, max_lines=18):
    if not key:
        return ""

    lines = [x.rstrip() for x in key.splitlines() if x.strip()]
    if not lines:
        return ""

    anchors = [
        "电源电压", "额定值", "允许范围", "下限", "上限",
        "输入电流", "输出电流", "功率", "功耗", "尺寸", "重量"
    ]

    hit = None
    for i, line in enumerate(lines):
        if any(a in line for a in anchors):
            hit = i
            break

    if hit is None:
        return "\n".join(lines[:max_lines])[:1200]

    start = max(0, hit - 2)
    end = min(len(lines), hit + max_lines)
    return "\n".join(lines[start:end])[:1200]



def print_figure_answer(q):
    results = query_figures(q, n=5)

    print("答案")
    print("-" * 80)

    if not results:
        print("没有找到足够相关的图文证据。")
        return

    top = results[0]
    meta = top["metadata"]
    doc = top["document"]

    page = meta.get("page")
    figure_id = meta.get("figure_id")
    visual_type = meta.get("visual_type")

    summary = field_from_doc(doc, "图像摘要")
    ports = field_from_doc(doc, "端子/接口")
    connections = field_from_doc(doc, "连接关系")
    visible_text = field_from_doc(doc, "图中文字")
    warnings = field_from_doc(doc, "警告/限制")

    ports_filtered = filter_field_by_question(ports, q, max_items=6, strict=True)
    connections_filtered = filter_field_by_question(connections, q, max_items=6, strict=False)
    visible_filtered = filter_field_by_question(visible_text, q, max_items=8, strict=False)
    warnings_filtered = filter_warnings_by_question(warnings, q, max_items=3)

    print(f"根据第 {page} 页图文证据，相关结论如下。")

    if summary:
        print(f"\n图示摘要：{summary}")

    if ports_filtered:
        print(f"\n相关端子/接口：\n{ports_filtered}")

    if connections_filtered:
        print(f"\n相关连接关系：\n{connections_filtered}")

    if visible_filtered:
        print(f"\n关键说明：\n{visible_filtered}")

    if warnings_filtered:
        print(f"\n注意事项：\n{warnings_filtered}")

    print("\n依据")
    print("-" * 80)
    print("- 路由：figure")
    print(f"- 页码：{page}")
    print(f"- figure_id：{figure_id}")
    print(f"- 图像类型：{visual_type}")
    print(f"- score：{top['score']:.4f}")
    print(f"- distance：{top['distance']:.4f}")

    print("\n补充图文证据")
    print("-" * 80)
    for i, r in enumerate(results[1:4], 2):
        m = r["metadata"]
        d = r["document"]
        s = field_from_doc(d, "图像摘要")
        print(
            f"[{i}] page={m.get('page')} "
            f"figure_id={m.get('figure_id')} "
            f"type={m.get('visual_type')} "
            f"score={r['score']:.4f}"
        )
        if s:
            print(f"    {s}")


def print_table_answer(q):
    raw = run_script(ASK_TABLE, q)

    answer = extract_block(raw, "答案")
    evidence = extract_block(raw, "依据")
    key = extract_block(raw, "关键证据")

    module_name = module_name_from_question_or_key(q, key)

    if module_name and answer:
        answer = re.sub(r"该模块\s*的", f"{module_name} 的", answer)
        answer = answer.replace("该模块 的", f"{module_name} 的")

    print("答案")
    print("-" * 80)
    if answer:
        print(answer)
    else:
        print(raw[:2000])

    if evidence:
        print("\n依据")
        print("-" * 80)
        print(evidence)

    if key:
        print("\n关键证据")
        print("-" * 80)
        print(compact_table_key_evidence(key, q))

    try:
        figs = query_figures(q, n=3)
        if figs:
            print("\n图文补充")
            print("-" * 80)
            for i, r in enumerate(figs, 1):
                m = r["metadata"]
                s = field_from_doc(r["document"], "图像摘要")
                print(
                    f"[{i}] page={m.get('page')} "
                    f"figure_id={m.get('figure_id')} "
                    f"type={m.get('visual_type')} "
                    f"score={r['score']:.4f}"
                )
                if s:
                    print(f"    {s}")
    except Exception as e:
        print("\n图文补充失败：", e)


def print_mixed_answer(q):
    print("文本回答")
    print("-" * 80)
    print(run_script(ASK_TEXT, q)[:2500])

    print("\n图文补充")
    print("-" * 80)
    try:
        figs = query_figures(q, n=3)
        for i, r in enumerate(figs, 1):
            m = r["metadata"]
            s = field_from_doc(r["document"], "图像摘要")
            print(
                f"[{i}] page={m.get('page')} "
                f"figure_id={m.get('figure_id')} "
                f"type={m.get('visual_type')} "
                f"score={r['score']:.4f}"
            )
            if s:
                print(f"    {s}")
    except Exception as e:
        print("图文补充失败：", e)


def main():
    q = " ".join(sys.argv[1:]).strip()
    if not q:
        q = input("请输入问题：").strip()

    mode = route(q)

    print(f"问题：{q}")
    print(f"路由：{mode}")
    print("=" * 80)

    if mode == "figure":
        print_figure_answer(q)
    elif mode == "table":
        print_table_answer(q)
    else:
        print_mixed_answer(q)


if __name__ == "__main__":
    main()
