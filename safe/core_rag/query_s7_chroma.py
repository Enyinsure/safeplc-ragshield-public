from pathlib import Path
import sys

import torch
import chromadb
from sentence_transformers import SentenceTransformer


HOME = Path.home()

DB_PATH = str(HOME / "s7_chroma_db")
COLLECTION_NAME = "s7_1500_manual"
MODEL_BASE_DIR = HOME / ".cache/modelscope/BAAI"

TARGET_MODEL = "CPU 1511-1 PN"
TARGET_ORDER_NO = "6ES7511-1AL03-0AB0"

BAD_TERMS = [
    "1511C-1 PN",
    "1511T-1 PN",
    "1511TF-1 PN",
    "1512C-1 PN",
    "1515R-2 PN",
    "1515T-2 PN",
    "1516-3 PN/DP",
    "1517H-3 PN",
    "接口模块",
    "模拟量模块",
    "尺寸图",
    "附件",
    "前言",
    "目录",
    "索引",
]

BOOST_TERMS = [
    TARGET_MODEL,
    TARGET_ORDER_NO,
    "技术规范",
    "技术数据",
    "商品编号",
    "订货号",
    "产品类型标志",
    "固件版本",
    "电源电压",
]


def find_embedding_model() -> str:
    candidates = list(MODEL_BASE_DIR.glob("bge-small-zh-v1*"))
    if not candidates:
        raise FileNotFoundError(f"找不到 embedding 模型目录：{MODEL_BASE_DIR}")
    return str(candidates[0])


def load_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_collection(COLLECTION_NAME)


def rerank_results(docs, metas, dists):
    ranked = []

    for doc, meta, dist in zip(docs, metas, dists):
        section = str(meta.get("section", ""))
        text_all = doc + "\n" + section

        score = -float(dist)

        for term in BOOST_TERMS:
            if term in text_all:
                score += 2.0

        if TARGET_MODEL in section:
            score += 4.0
        if TARGET_ORDER_NO in section:
            score += 4.0
        if "技术规范" in section or "技术数据" in section:
            score += 2.0

        for term in BAD_TERMS:
            if term in text_all:
                score -= 3.0

        ranked.append({
            "score": score,
            "distance": float(dist),
            "document": doc,
            "metadata": meta,
            "section": section,
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def filter_exact_hits(ranked):
    exact_hits = []

    for item in ranked:
        doc = item["document"]
        section = item["section"]
        text_all = doc + "\n" + section

        has_target = TARGET_MODEL in text_all and TARGET_ORDER_NO in text_all

        has_spec = (
            "技术数据" in section
            or "技术规范" in section
            or "技术数据" in doc[:400]
            or "技术规范" in doc[:400]
        )

        is_bad_section = any(
            x in section
            for x in ["尺寸图", "附件", "前言", "目录", "索引"]
        )

        if has_target and has_spec and not is_bad_section:
            exact_hits.append(item)

    return exact_hits if exact_hits else ranked


def search(query: str, n_results: int = 30, final_top_k: int = 5):
    model_path = find_embedding_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("device:", device)
    print("model_path:", model_path)
    print("query:", query)

    model = SentenceTransformer(model_path, device=device)
    collection = load_collection()

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    ).tolist()

    res = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    ranked = rerank_results(docs, metas, dists)
    final_results = filter_exact_hits(ranked)

    print("\n" + "#" * 80)
    print("最终结果")
    print("#" * 80)

    for i, item in enumerate(final_results[:final_top_k], start=1):
        meta = item["metadata"]
        doc = item["document"]

        print("=" * 80)
        print("rank:", i)
        print("rerank_score:", item["score"])
        print("vector_distance:", item["distance"])
        print("page:", meta.get("page_no"))
        print("section:", meta.get("section"))
        print("-" * 80)
        print(doc[:1200])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_text = " ".join(sys.argv[1:])
    else:
        query_text = (
            "CPU 1511-1 PN 6ES7511-1AL03-0AB0 "
            "技术规范 商品编号 订货号 固件版本 电源电压"
        )

    search(query_text)
