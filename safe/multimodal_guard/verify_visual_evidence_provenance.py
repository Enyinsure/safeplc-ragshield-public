#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Visual Evidence Card provenance for a single evidence id."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from safe.trusted_rag.local_env import load_local_env, resolve_safe_path


def _configured_path(name: str, fallback: str) -> Path:
    value = load_local_env().get(name, "").strip() or fallback
    return resolve_safe_path(value)


def _find_card(cards_path: Path, evidence_id: str, warnings: List[str]) -> Dict[str, Any] | None:
    if not cards_path.exists():
        warnings.append(f"visual cards JSONL not found: {cards_path}")
        return None
    with cards_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                card = json.loads(line)
            except Exception as exc:
                warnings.append(f"line {line_no}: invalid JSON: {exc}")
                continue
            if str(card.get("evidence_id", card.get("id", ""))) == evidence_id:
                return card
    warnings.append(f"evidence_id not found in visual cards: {evidence_id}")
    return None


def _chroma_has_record(evidence_id: str, warnings: List[str]) -> bool | None:
    env = load_local_env()
    chroma_dir = _configured_path("SAFE_VISUAL_CHROMA_DIR_V2", "safe/data/chroma_visual_cards_v2_not_configured")
    if not chroma_dir.exists():
        warnings.append(f"visual Chroma path not found: {chroma_dir}")
        return None
    try:
        import chromadb  # type: ignore
    except Exception as exc:
        warnings.append(f"chromadb unavailable: {exc}")
        return None
    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        collection = client.get_collection(env.get("SAFE_VISUAL_COLLECTION_V2", "s7_visual_cards_v2"))
        by_id = collection.get(ids=[evidence_id])
        if by_id.get("ids"):
            return True
        by_meta = collection.get(where={"evidence_id": evidence_id})
        return bool(by_meta.get("ids"))
    except Exception as exc:
        warnings.append(f"Chroma provenance lookup failed: {exc}")
        return None


def verify_provenance(evidence_id: str) -> Dict[str, Any]:
    warnings: List[str] = []
    cards_path = _configured_path("SAFE_VISUAL_CARDS_V2", "safe/data/visual_cards_v2_not_configured.jsonl")
    card = _find_card(cards_path, evidence_id, warnings)
    if not card:
        return {
            "evidence_id": evidence_id,
            "page": "",
            "section": "",
            "visual_type": "",
            "image_exists": False,
            "text_hash_ok": False,
            "evidence_hash_ok": False,
            "chroma_record_exists": False,
            "warnings": warnings,
            "result": "WARN",
        }

    image_path = str(card.get("source_image_path", "")).strip()
    image_exists = resolve_safe_path(image_path).exists() if image_path else False
    if not image_path:
        warnings.append("source_image_path is empty")
    elif not image_exists:
        warnings.append(f"source image path does not exist: {image_path}")
    for field in ["page", "section", "visual_type", "text"]:
        if not str(card.get(field, "")).strip():
            warnings.append(f"{field} is empty")
    text_hash_ok = bool(str(card.get("text_hash", "")).strip())
    evidence_hash_ok = bool(str(card.get("hash", card.get("evidence_hash", ""))).strip())
    if not text_hash_ok:
        warnings.append("text_hash is empty")
    if not evidence_hash_ok:
        warnings.append("hash/evidence_hash is empty")
    chroma_exists = _chroma_has_record(evidence_id, warnings)
    required_ok = all(str(card.get(field, "")).strip() for field in ["page", "section", "visual_type", "text"])
    required_ok = required_ok and text_hash_ok and evidence_hash_ok
    result = "PASS" if required_ok and image_exists and chroma_exists is True and not warnings else "WARN"
    if not required_ok:
        result = "FAIL"
    return {
        "evidence_id": evidence_id,
        "page": card.get("page", ""),
        "section": card.get("section", ""),
        "visual_type": card.get("visual_type", ""),
        "image_exists": image_exists,
        "text_hash_ok": text_hash_ok,
        "evidence_hash_ok": evidence_hash_ok,
        "chroma_record_exists": chroma_exists is True,
        "warnings": warnings,
        "result": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence_id", required=True)
    args = parser.parse_args()
    result = verify_provenance(args.evidence_id)
    for key in [
        "evidence_id",
        "page",
        "section",
        "visual_type",
        "image_exists",
        "text_hash_ok",
        "evidence_hash_ok",
        "chroma_record_exists",
        "warnings",
        "result",
    ]:
        print(f"{key} = {result[key]}")
    return 1 if result["result"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

