import json
import re
from pathlib import Path

HOME = Path.home()

PAGE_DIR = HOME / "s7_multimodal_v1/images/visual_candidate_pages"
SEL = HOME / "s7_multimodal_v1/eval/selected_visual_pages.txt"
OUT = HOME / "s7_multimodal_v1/figure_cards/selected_visual_manifest.jsonl"

OUT.parent.mkdir(parents=True, exist_ok=True)

if not PAGE_DIR.exists():
    raise FileNotFoundError(f"missing page image dir: {PAGE_DIR}")

if not SEL.exists():
    raise FileNotFoundError(f"missing selected pages file: {SEL}")

pages = []
bad_lines = []

for line in SEL.read_text(encoding="utf-8", errors="ignore").splitlines():
    raw = line.strip()
    if not raw or raw.startswith("#"):
        continue

    # 兼容 page_0208、208、以及误写入的 EOF
    m = re.search(r"(\d+)", raw)
    if not m:
        bad_lines.append(raw)
        continue

    p = int(m.group(1))
    if p not in pages:
        pages.append(p)

records = []
missing = []

for p in pages:
    img = PAGE_DIR / f"page_{p:04d}.jpg"

    if not img.exists():
        missing.append(p)
        continue

    records.append({
        "doc_id": "1500_manual_collection_zh-CHS",
        "page": p,
        "figure_id": f"page_{p:04d}_visual",
        "image_path": str(img),
        "source_type": "rendered_pdf_page",
        "visual_type": "",
        "caption": "",
        "nearby_text": "",
        "needs_vlm": True,
        "notes": "人工筛选出的视觉高价值页，等待 VLM 生成结构化语义描述"
    })

with OUT.open("w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("selected page lines:", len(pages))
print("valid records:", len(records))
print("manifest:", OUT)

if missing:
    print("missing page images:", missing)

if bad_lines:
    print("ignored non-page lines:", bad_lines)
