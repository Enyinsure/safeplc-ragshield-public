import re
import sys
from pathlib import Path

import torch
import chromadb
from sentence_transformers import SentenceTransformer

HOME = Path.home()

DB_PATH = str(HOME / "s7_multimodal_v1/index/chroma_figures_v1")
COLLECTION_NAME = "s7_figures_v1"
MODEL_BASE_DIR = HOME / ".cache/modelscope/BAAI"


def find_embedding_model() -> str:
    candidates = list(MODEL_BASE_DIR.glob("bge-small-zh-v1*"))
    if not candidates:
        raise FileNotFoundError(f"找不到 embedding 模型目录：{MODEL_BASE_DIR}")
    return str(candidates[0])


def extract_boost_terms(q: str):
    terms = []

    # 型号类：CPU 1517-3 PN、CPU 1517-3 PN/DP、PS 60W...
    for pat in [
        r"CPU\s*\d+[A-Z]?(?:-\d+)?\s*(?:PN|DP|PN/DP|T|TF|HF|H|R)?",
        r"PS\s*\d+\s*W?\s*[\d/]*\s*(?:VDC|DC|AC/DC|HF)?",
        r"ET\s*200MP",
        r"PROFINET",
        r"PROFIBUS",
        r"FastConnect",
        r"RJ45",
        r"24\s*V\s*DC",
        r"X\d",
        r"P\dR?",
    ]:
        for m in re.findall(pat, q, flags=re.I):
            t = re.sub(r"\s+", " ", m.strip())
            if t:
                terms.append(t)

    for t in ["接口", "端子", "接线", "引脚", "针脚", "拓扑", "环网", "电源电压"]:
        if t in q:
            terms.append(t)

    # 去重
    out = []
    seen = set()
    for t in terms:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


def rerank(q, docs, metas, dists):
    boost_terms = extract_boost_terms(q)
    ranked = []

    for doc, meta, dist in zip(docs, metas, dists):
        text = doc + "\n" + " ".join(str(v) for v in meta.values())
        text_low = text.lower()

        score = -float(dist)

        for t in boost_terms:
            tl = t.lower()
            if tl in text_low:
                score += 2.5

        # 精确型号更重要
        for t in boost_terms:
            if t.lower().startswith("cpu") or t.lower().startswith("ps"):
                if t.lower() in text_low:
                    score += 5.0

        # 接口类问题优先 wiring_diagram / terminal_assignment / interface_layout
        if any(x in q for x in ["接口", "端子", "接线", "引脚", "针脚", "X1", "X2", "X3"]):
            if meta.get("visual_type") in ["wiring_diagram", "terminal_assignment", "interface_layout"]:
                score += 1.5

        # 降低明显不匹配型号
        if "CPU 1517-3" in q and "CPU 1517-3" not in text and "1517-3" not in text:
            score -= 4.0
        if "PN/DP" in q and "PN/DP" not in text:
            score -= 2.0

        ranked.append((score, doc, meta, dist))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked


def main():
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = "CPU 1517-3 PN 的 PROFINET 接口 X1 X2"

    model_path = find_embedding_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("device:", device)
    print("model_path:", model_path)

    model = SentenceTransformer(model_path, device=device)

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()

    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    # 先多取，再 rerank
    res = collection.query(
        query_embeddings=query_embedding,
        n_results=12,
        include=["documents", "metadatas", "distances"],
    )

    ranked = rerank(
        query,
        res["documents"][0],
        res["metadatas"][0],
        res["distances"][0],
    )[:5]

    print("query:", query)
    print("boost_terms:", extract_boost_terms(query))
    print("=" * 90)

    for i, (score, doc, meta, dist) in enumerate(ranked, 1):
        print(f"[{i}] score={score:.4f} distance={dist:.4f}")
        print("page:", meta.get("page"))
        print("figure_id:", meta.get("figure_id"))
        print("visual_type:", meta.get("visual_type"))
        print("image_path:", meta.get("image_path"))
        print("text:")
        print(doc[:1000])
        print("-" * 90)


if __name__ == "__main__":
    main()
