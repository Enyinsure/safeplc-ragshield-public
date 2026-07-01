import json
import re
from pathlib import Path

IN = Path.home() / "s7_table_stitch_output_v4_middle" / "stitched_tables.json"
OUT = Path.home() / "s7_rag_processed" / "s7_table_chunks_v4.jsonl"

def clean_html_table(s: str) -> str:
    s = s.replace("&quot;", '"').replace("&nbsp;", " ")
    s = re.sub(r"<img[^>]*>", "[图标]", s)
    s = re.sub(r"</tr>", "\n", s, flags=re.I)
    s = re.sub(r"</t[dh]>", " | ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+\|", " |", s)
    s = re.sub(r"\|\s+\|", "| |", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()

data = json.loads(IN.read_text(encoding="utf-8"))

rows = []
for item in data:
    pages = item.get("pages", [])
    if item.get("num_parts", 1) <= 1:
        continue

    raw = item.get("merged_text", "")
    text = clean_html_table(raw)

    if not text:
        continue

    table_id = item.get("id", "")
    page_label = "-".join(map(str, pages))

    chunk = {
        "id": f"s7_table_v4_{table_id}",
        "text": (
            f"跨页表格：{table_id}\n"
            f"页码范围：{page_label}\n"
            f"合并原因：{item.get('reason', '')}\n\n"
            f"{text}"
        ),
        "metadata": {
            "source": "S7-1500/ET 200MP Manual Collection - stitched tables v4",
            "chunk_type": "stitched_table",
            "table_id": table_id,
            "pages": pages,
            "page_no": pages[0] if pages else None,
            "page_range": page_label,
            "num_parts": item.get("num_parts"),
            "score": item.get("score"),
            "source_file": item.get("source_file"),
        }
    }
    rows.append(chunk)

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("written:", OUT)
print("table chunks:", len(rows))
