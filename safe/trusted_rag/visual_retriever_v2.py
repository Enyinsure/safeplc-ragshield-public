#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Visual evidence retriever v2 with graceful Chroma fallback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from . import paths
from .hash_chain import sha256_text


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def _score_from_distance(distance: Any) -> float:
    try:
        return round(1.0 / (1.0 + float(distance)), 6)
    except Exception:
        return 0.0


def _normalise_visual(
    evidence_id: str,
    text: str,
    metadata: Dict[str, Any],
    score: float,
) -> Dict[str, Any]:
    page = metadata.get("page", metadata.get("page_id", metadata.get("page_no", "")))
    text = text or metadata.get("text", "") or metadata.get("ocr_text", "")
    text_hash = sha256_text(str(text))
    payload = {
        "evidence_id": str(evidence_id),
        "source_type": str(metadata.get("source_type", "visual_chroma_v2")),
        "modality": str(metadata.get("modality", "image")),
        "visual_type": str(metadata.get("visual_type", metadata.get("type", "unknown"))),
        "page": page,
        "section": str(metadata.get("section", "")),
        "text": str(text),
        "score": float(score),
        "source_image_path": str(metadata.get("source_image_path", metadata.get("image_path", ""))),
        "text_hash": text_hash,
    }
    payload["hash"] = sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def retrieve_visual_evidence(query: str, n: int = 3) -> List[Dict[str, Any]]:
    chroma_dir = paths.VISUAL_CHROMA_DIR_V2
    collection_name = str(paths.VISUAL_COLLECTION_V2 or "s7_visual_cards_v2")
    if not chroma_dir.exists():
        _warn(f"visual Chroma path does not exist: {chroma_dir}")
        return []
    try:
        import chromadb  # type: ignore
    except Exception as exc:
        _warn(f"chromadb is unavailable: {exc}")
        return []

    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        collection = client.get_collection(collection_name)
        result = collection.query(query_texts=[query], n_results=n)
    except Exception as exc:
        _warn(f"visual Chroma query failed: {exc}")
        return []

    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    evidence: List[Dict[str, Any]] = []
    for index, doc in enumerate(docs):
        metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
        evidence_id = ids[index] if index < len(ids) else f"visual_{index + 1}"
        distance = distances[index] if index < len(distances) else None
        evidence.append(_normalise_visual(evidence_id, doc or "", metadata, _score_from_distance(distance)))
    return evidence


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--n", type=int, default=3)
    args = parser.parse_args(argv)
    results = retrieve_visual_evidence(args.query, n=args.n)
    for rank, item in enumerate(results, start=1):
        print(f"rank: {rank}")
        print(f"evidence_id: {item['evidence_id']}")
        print(f"visual_type: {item['visual_type']}")
        print(f"page: {item['page']}")
        print(f"section: {item['section']}")
        print(f"score: {item['score']}")
        print(f"image: {item['source_image_path']}")
        print(f"hash: {item['hash']}")
        print(f"text: {item['text'][:220]}")
        print()
    if not results:
        print("visual_evidence_count = 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
