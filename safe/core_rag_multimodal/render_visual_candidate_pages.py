import re
from pathlib import Path
import fitz

HOME = Path.home()

PDF = HOME / "1500_manual_collection_zh-CHS_zh-CHS.pdf"
CAND = HOME / "s7_multimodal_v1/eval/visual_page_candidates.txt"
OUT = HOME / "s7_multimodal_v1/images/visual_candidate_pages"

OUT.mkdir(parents=True, exist_ok=True)

if not PDF.exists():
    raise FileNotFoundError(f"PDF not found: {PDF}")

if not CAND.exists():
    raise FileNotFoundError(f"candidate file not found: {CAND}")

pages = []
for line in CAND.read_text(encoding="utf-8", errors="ignore").splitlines():
    m = re.search(r"page=(\d+)", line)
    if not m:
        continue
    p = int(m.group(1))
    if p not in pages:
        pages.append(p)
    if len(pages) >= 80:
        break

print("candidate pages:", pages[:20])
print("total selected for rendering:", len(pages))

doc = fitz.open(str(PDF))
rendered = 0
skipped = 0

for p in pages:
    # s7_full_pages.jsonl 里的页码通常是 1-based，PyMuPDF 是 0-based
    idx = p - 1

    if idx < 0 or idx >= len(doc):
        print("skip out of range:", p)
        skipped += 1
        continue

    page = doc[idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)

    out = OUT / f"page_{p:04d}.jpg"
    pix.save(str(out))

    rendered += 1
    print("rendered:", out)

doc.close()

print("done")
print("rendered:", rendered)
print("skipped:", skipped)
print("out_dir:", OUT)
