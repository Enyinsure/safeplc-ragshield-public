import json
from pathlib import Path

HOME = Path.home()

INP = HOME / "s7_multimodal_v1/figure_cards/selected_visual_manifest.jsonl"
OUT = HOME / "s7_multimodal_v1/figure_cards/selected_visual_manifest_enriched.jsonl"

PAGE_CANDIDATES = [
    HOME / "s7_full_pages.jsonl",
    HOME / "s7_rag_processed/s7_full_pages.jsonl",
    HOME / "s7_rag_processed/full_pages.jsonl",
]

PAGE_FILE = None
for p in PAGE_CANDIDATES:
    if p.exists():
        PAGE_FILE = p
        break

if PAGE_FILE is None:
    raise FileNotFoundError("找不到 s7_full_pages.jsonl，请先 find ~ -name 's7_full_pages.jsonl'")

page_text = {}

with PAGE_FILE.open("r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if not line.strip():
            continue
        obj = json.loads(line)
        page = obj.get("page") or obj.get("page_no") or obj.get("page_idx") or obj.get("pageno")
        text = obj.get("text") or obj.get("content") or obj.get("page_text") or ""

        if page is None:
            continue

        try:
            page = int(page)
        except Exception:
            continue

        page_text[page] = text.strip()

records = []

with INP.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        rec = json.loads(line)
        p = int(rec["page"])

        ctx_parts = []
        for pp in [p - 1, p, p + 1]:
            txt = page_text.get(pp, "")
            if txt:
                ctx_parts.append(f"[page {pp}]\n{txt[:1800]}")

        rec["nearby_text"] = "\n\n".join(ctx_parts)
        records.append(rec)

with OUT.open("w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("page_file:", PAGE_FILE)
print("records:", len(records))
print("out:", OUT)
