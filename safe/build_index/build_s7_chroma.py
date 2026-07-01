import json
from pathlib import Path

import torch
import chromadb
from sentence_transformers import SentenceTransformer

HOME = Path.home()

chunks_path = HOME / "s7_full_chunks.jsonl"
db_path = str(HOME / "s7_chroma_db")

# 自动寻找 ModelScope 下载的 bge-small-zh-v1.5 路径
model_candidates = list((HOME / ".cache/modelscope/BAAI").glob("bge-small-zh-v1*"))
if not model_candidates:
    raise FileNotFoundError("找不到 bge-small-zh-v1.5 模型目录，请先确认模型已下载。")

model_path = str(model_candidates[0])

device = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", device)
print("model_path:", model_path)
print("chunks_path:", chunks_path)
print("db_path:", db_path)

model = SentenceTransformer(model_path, device=device)

client = chromadb.PersistentClient(path=db_path)

# 重建 collection，避免重复插入
try:
    client.delete_collection("s7_1500_manual")
    print("deleted old collection")
except Exception:
    pass

collection = client.get_or_create_collection(
    name="s7_1500_manual",
    metadata={"hnsw:space": "cosine"}
)

batch_size = 128
ids, docs, metas = [], [], []
total = 0

def flush():
    global ids, docs, metas, total
    if not ids:
        return

    embeddings = model.encode(
        docs,
        batch_size=128,
        normalize_embeddings=True,
        show_progress_bar=False
    ).tolist()

    collection.add(
        ids=ids,
        documents=docs,
        metadatas=metas,
        embeddings=embeddings
    )

    total += len(ids)
    print(f"inserted: {total}")

    ids, docs, metas = [], [], []

with chunks_path.open("r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        meta = item["metadata"]

        ids.append(item["id"])
        docs.append(item["text"])
        metas.append({
            "source": str(meta.get("source", "")),
            "pdf_path": str(meta.get("pdf_path", "")),
            "page_no": int(meta.get("page_no", 0)),
            "page_index": int(meta.get("page_index", 0)),
            "section": str(meta.get("section", "")),
            "chunk_index": int(meta.get("chunk_index", 0)),
        })

        if len(ids) >= batch_size:
            flush()

flush()

print("done")
print("collection count:", collection.count())
