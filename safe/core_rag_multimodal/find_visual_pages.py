import json
from pathlib import Path
from collections import Counter

HOME = Path.home()
CANDIDATES = [
    HOME / "s7_full_pages.jsonl",
    HOME / "s7_rag_processed/s7_full_pages.jsonl",
    HOME / "s7_rag_processed/full_pages.jsonl",
]

PAGE_FILE = None
for p in CANDIDATES:
    if p.exists():
        PAGE_FILE = p
        break

if PAGE_FILE is None:
    raise FileNotFoundError("找不到 s7_full_pages.jsonl，请先用 find ~/ -name 's7_full_pages.jsonl' 确认路径")

KEYWORDS = [
    "接线图", "接线", "端子", "端子分配", "接口", "前视图", "正视图",
    "连接", "插头", "针脚", "引脚", "PROFINET", "PN/IE",
    "电源", "负载电源", "系统电源", "CPU 1511", "CPU 1513", "CPU 1515",
    "ET 200MP", "IM 155", "示意图", "图 "
]

rows = []
with PAGE_FILE.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        obj = json.loads(line)
        page = obj.get("page") or obj.get("page_no") or obj.get("page_idx") or obj.get("pageno")
        text = obj.get("text") or obj.get("content") or obj.get("page_text") or ""
        if isinstance(page, int) and page == 0:
            page = 1
        score = 0
        hits = []
        for kw in KEYWORDS:
            c = text.count(kw)
            if c:
                score += c
                hits.append(f"{kw}:{c}")
        if score:
            snippet = text[:300].replace("\n", " ")
            rows.append((score, page, hits, snippet))

rows.sort(reverse=True, key=lambda x: x[0])

out = HOME / "s7_multimodal_v1/eval/visual_page_candidates.txt"
out.parent.mkdir(parents=True, exist_ok=True)

with out.open("w", encoding="utf-8") as w:
    for score, page, hits, snippet in rows[:200]:
        w.write(f"page={page}\tscore={score}\thits={','.join(hits)}\n")
        w.write(snippet + "\n\n")

print("page_file:", PAGE_FILE)
print("written:", out)
print("top 30:")
for score, page, hits, snippet in rows[:30]:
    print(f"page={page}\tscore={score}\thits={','.join(hits[:8])}")
