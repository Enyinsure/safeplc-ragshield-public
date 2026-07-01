import json
from pathlib import Path

HOME = Path.home()

INP = HOME / "s7_multimodal_v1/figure_cards/figure_cards_v1.jsonl"
OUT = HOME / "s7_multimodal_v1/chunks/s7_figure_chunks_v1.jsonl"

OUT.parent.mkdir(parents=True, exist_ok=True)


def compact_items(items, max_items=8):
    if not isinstance(items, list):
        return ""
    parts = []
    for x in items[:max_items]:
        if isinstance(x, str):
            parts.append(x)
        elif isinstance(x, dict):
            vals = []
            for k in ["name", "type", "description", "source", "target", "destination"]:
                v = x.get(k)
                if v:
                    vals.append(str(v))
            if vals:
                parts.append(" / ".join(vals))
        else:
            parts.append(str(x))
    return "；".join(parts)


def build_text(card):
    page = card.get("page")
    visual_type = card.get("visual_type", "unknown")
    summary = card.get("summary_zh", "")
    objects = compact_items(card.get("objects"), 8)
    connections = compact_items(card.get("connections"), 8)
    ports = compact_items(card.get("ports_interfaces"), 8)
    visible_text = compact_items(card.get("visible_text"), 10)
    warnings = compact_items(card.get("warnings_or_limits"), 6)
    terms = compact_items(card.get("query_terms"), 12)

    fallback_note = ""
    if card.get("fallback_from_parse_failed"):
        fallback_note = "注意：该页 VLM 输出使用保守兜底卡片，需要人工复核。"

    parts = [
        f"资料：S7-1500 / ET 200MP 中文手册",
        f"页码：{page}",
        f"图像类型：{visual_type}",
        f"图像摘要：{summary}",
    ]

    if objects:
        parts.append(f"可见对象：{objects}")
    if connections:
        parts.append(f"连接关系：{connections}")
    if ports:
        parts.append(f"端子/接口：{ports}")
    if visible_text:
        parts.append(f"图中文字：{visible_text}")
    if warnings:
        parts.append(f"警告/限制：{warnings}")
    if terms:
        parts.append(f"检索关键词：{terms}")
    if fallback_note:
        parts.append(fallback_note)

    return "\n".join(parts)


records = []

with INP.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        card = json.loads(line)
        chunk_id = "fig_" + str(card.get("figure_id"))

        text_for_embedding = build_text(card)

        display_text = (
            f"第 {card.get('page')} 页视觉图示："
            f"{card.get('summary_zh') or '该页包含手册中的图示信息'}"
        )

        rec = {
            "chunk_id": chunk_id,
            "source_type": "figure",
            "doc_id": card.get("doc_id", "1500_manual_collection_zh-CHS"),
            "page": card.get("page"),
            "figure_id": card.get("figure_id"),
            "image_path": card.get("image_path"),
            "visual_type": card.get("visual_type", "unknown"),
            "text_for_embedding": text_for_embedding,
            "display_text": display_text,
            "metadata": {
                "source_type": "figure",
                "doc_id": card.get("doc_id", "1500_manual_collection_zh-CHS"),
                "page": card.get("page"),
                "figure_id": card.get("figure_id"),
                "image_path": card.get("image_path"),
                "visual_type": card.get("visual_type", "unknown"),
                "query_terms": card.get("query_terms", []),
                "needs_human_review": card.get("needs_human_review", False),
                "fallback_from_parse_failed": card.get("fallback_from_parse_failed", False),
            }
        }

        records.append(rec)

with OUT.open("w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("written:", OUT)
print("records:", len(records))
