#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Visual Evidence DB coverage report with graceful fallbacks."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from safe.trusted_rag.local_env import SAFE_DIR, load_local_env, resolve_safe_path


KNOWN_TOTAL_PAGES = 13009


def _configured_path(name: str, fallback: str) -> Path:
    value = load_local_env().get(name, "").strip() or fallback
    return resolve_safe_path(value)


def _read_cards(path: Path, warnings: List[str]) -> List[Dict[str, Any]]:
    if not path.exists():
        warnings.append(f"visual cards JSONL not found: {path}")
        return []
    cards: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                cards.append(json.loads(stripped))
            except Exception as exc:
                warnings.append(f"line {line_no}: invalid JSON: {exc}")
    return cards


def _count_chroma(path: Path, collection_name: str, warnings: List[str]) -> int | None:
    if not path.exists():
        warnings.append(f"visual Chroma path not found: {path}")
        return None
    try:
        import chromadb  # type: ignore
    except Exception as exc:
        warnings.append(f"chromadb unavailable: {exc}")
        return None
    try:
        client = chromadb.PersistentClient(path=str(path))
        collection = client.get_collection(collection_name)
        return int(collection.count())
    except Exception as exc:
        warnings.append(f"visual Chroma count failed: {exc}")
        return None


def _contains_any(card: Dict[str, Any], keywords: Iterable[str]) -> bool:
    text = json.dumps(card, ensure_ascii=False).lower()
    return any(keyword.lower() in text for keyword in keywords)


def build_coverage(cards_path: Path | None = None) -> Dict[str, Any]:
    env = load_local_env()
    warnings: List[str] = []
    cards = _read_cards(cards_path or _configured_path("SAFE_VISUAL_CARDS_V2", "safe/data/visual_cards_v2_not_configured.jsonl"), warnings)
    chroma_dir = _configured_path("SAFE_VISUAL_CHROMA_DIR_V2", "safe/data/chroma_visual_cards_v2_not_configured")
    collection_name = env.get("SAFE_VISUAL_COLLECTION_V2", "s7_visual_cards_v2")
    chroma_count = _count_chroma(chroma_dir, collection_name, warnings)

    visual_types = Counter(str(card.get("visual_type", "") or "unknown") for card in cards)
    source_types = Counter(str(card.get("source_type", "") or "unknown") for card in cards)
    sections = Counter(str(card.get("section", "") or "unknown") for card in cards)

    summary = {
        "total_pages": KNOWN_TOTAL_PAGES if cards else "unknown",
        "visual_card_count": len(cards),
        "chroma_count": chroma_count,
        "chroma_count_matches_cards": chroma_count == len(cards) if chroma_count is not None else False,
        "visual_type_distribution": dict(visual_types.most_common()),
        "source_type_distribution": dict(source_types.most_common()),
        "section_top_20": dict(sections.most_common(20)),
        "risk_related_evidence_count": sum(_contains_any(card, ["warning", "alarm", "fault", "diagnostic", "risk", "error"]) for card in cards),
        "wiring_or_terminal_evidence_count": sum(_contains_any(card, ["wiring", "terminal", "接线", "端子"]) for card in cards),
        "diagnostic_alarm_evidence_count": sum(_contains_any(card, ["diagnostic", "alarm", "fault", "诊断", "报警", "故障"]) for card in cards),
        "module_cpu_evidence_count": sum(_contains_any(card, ["module", "cpu", "模块"]) for card in cards),
        "image_path_nonempty_count": sum(bool(str(card.get("source_image_path", "")).strip()) for card in cards),
        "image_path_exists_count": sum(
            bool(str(card.get("source_image_path", "")).strip()) and resolve_safe_path(str(card.get("source_image_path"))).exists()
            for card in cards
        ),
        "text_hash_nonempty_count": sum(bool(str(card.get("text_hash", "")).strip()) for card in cards),
        "hash_nonempty_count": sum(bool(str(card.get("hash", card.get("evidence_hash", ""))).strip()) for card in cards),
        "warnings": warnings,
    }
    return summary


def write_report(summary: Dict[str, Any], out_md: Path, out_json: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Visual Evidence DB Coverage Report",
        "",
        f"- total_pages: {summary['total_pages']}",
        f"- visual_card_count: {summary['visual_card_count']}",
        f"- chroma_count: {summary['chroma_count']}",
        f"- chroma_count_matches_cards: {summary['chroma_count_matches_cards']}",
        f"- risk_related_evidence_count: {summary['risk_related_evidence_count']}",
        f"- wiring_or_terminal_evidence_count: {summary['wiring_or_terminal_evidence_count']}",
        f"- diagnostic_alarm_evidence_count: {summary['diagnostic_alarm_evidence_count']}",
        f"- module_cpu_evidence_count: {summary['module_cpu_evidence_count']}",
        f"- image_path_nonempty_count: {summary['image_path_nonempty_count']}",
        f"- image_path_exists_count: {summary['image_path_exists_count']}",
        f"- text_hash_nonempty_count: {summary['text_hash_nonempty_count']}",
        f"- hash_nonempty_count: {summary['hash_nonempty_count']}",
        "",
        "## Visual Type Distribution",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in summary["visual_type_distribution"].items())
    lines.extend(["", "## Source Type Distribution", ""])
    lines.extend(f"- {key}: {value}" for key, value in summary["source_type_distribution"].items())
    lines.extend(["", "## Section Top 20", ""])
    lines.extend(f"- {key}: {value}" for key, value in summary["section_top_20"].items())
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in summary["warnings"] or ["none"])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards")
    parser.add_argument("--out_md")
    parser.add_argument("--out_json")
    args = parser.parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_md = resolve_safe_path(args.out_md) if args.out_md else SAFE_DIR / "reports" / f"VISUAL_DB_COVERAGE_REPORT_{stamp}.md"
    out_json = resolve_safe_path(args.out_json) if args.out_json else SAFE_DIR / "reports" / f"VISUAL_DB_COVERAGE_SUMMARY_{stamp}.json"
    summary = build_coverage(resolve_safe_path(args.cards) if args.cards else None)
    write_report(summary, out_md, out_json)
    print(f"visual_card_count = {summary['visual_card_count']}")
    print(f"chroma_count = {summary['chroma_count']}")
    print(f"warnings = {len(summary['warnings'])}")
    print(f"out_md = {out_md}")
    print(f"out_json = {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

