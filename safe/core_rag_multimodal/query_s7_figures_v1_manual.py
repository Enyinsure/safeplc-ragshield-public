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


def main():
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = "PROFINET 环网如何连接 HMI 设备"

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

    res = collection.query(
        query_embeddings=query_embedding,
        n_results=5,
        include=["documents", "metadatas", "distances"],
    )

    print("query:", query)
    print("=" * 90)

    for i, (doc, meta, dist) in enumerate(
        zip(res["documents"][0], res["metadatas"][0], res["distances"][0]),
        1
    ):
        print(f"[{i}] distance={dist:.4f}")
        print("page:", meta.get("page"))
        print("figure_id:", meta.get("figure_id"))
        print("visual_type:", meta.get("visual_type"))
        print("image_path:", meta.get("image_path"))
        print("text:")
        print(doc[:1000])
        print("-" * 90)


if __name__ == "__main__":
    main()
