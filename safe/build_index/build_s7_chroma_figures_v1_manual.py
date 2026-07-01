import json
from pathlib import Path

import torch
import chromadb
from sentence_transformers import SentenceTransformer

HOME = Path.home()

CHUNKS = HOME / "s7_multimodal_v1/chunks/s7_figure_chunks_v1.jsonl"
DB_PATH = str(HOME / "s7_multimodal_v1/index/chroma_figures_v1")
COLLECTION_NAME = "s7_figures_v1"

MODEL_BASE_DIR = HOME / ".cache/modelscope/BAAI"


def find_embedding_model() -> str:
    candidates = list(MODEL_BASE_DIR.glob("bge-small-zh-v1*"))
    if not candidates:
        raise FileNotFoundError(f"找不到 bge-small-zh-v1.5 模型目录：{MODEL_BASE_DIR}")
    return str(candidates[0])


def clean_meta(meta):
    out = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, list):
            out[k] = "；".join(str(x) for x in v)
        else:
            out[k] = str(v)
    return out


def main():
    if not CHUNKS.exists():
        raise FileNotFoundError(f"找不到图文 chunks：{CHUNKS}")

    model_path = find_embedding_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("device:", device)
    print("model_path:", model_path)
    print("chunks:", CHUNKS)
    print("db_path:", DB_PATH)
    print("collection:", COLLECTION_NAME)

    records = []
    with CHUNKS.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print("records:", len(records))

    model = SentenceTransformer(model_path, device=device)

    client = chromadb.PersistentClient(path=DB_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
        print("deleted old collection")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    batch_size = 32
    total = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        ids = [r["chunk_id"] for r in batch]
        docs = [r["text_for_embedding"] for r in batch]

        metas = []
        for r in batch:
            meta = dict(r.get("metadata", {}))
            meta.update({
                "chunk_id": r.get("chunk_id"),
                "source_type": "figure",
                "doc_id": r.get("doc_id"),
                "page": int(r.get("page") or 0),
                "figure_id": r.get("figure_id"),
                "image_path": r.get("image_path"),
                "visual_type": r.get("visual_type", "unknown"),
            })
            metas.append(clean_meta(meta))

        embeddings = model.encode(
            docs,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        collection.add(
            ids=ids,
            documents=docs,
            metadatas=metas,
            embeddings=embeddings,
        )

        total += len(batch)
        print(f"inserted: {total}")

    print("done")
    print("collection count:", collection.count())


if __name__ == "__main__":
    main()
