import re
from pathlib import Path
import fitz

HOME = Path.home()
PDF = HOME / "1500_manual_collection_zh-CHS_zh-CHS.pdf"
SEL = HOME / "s7_multimodal_v1/eval/selected_visual_pages.txt"
OUT = HOME / "s7_multimodal_v1/images/visual_candidate_pages"

OUT.mkdir(parents=True, exist_ok=True)

pages = []
for line in SEL.read_text(encoding="utf-8", errors="ignore").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    m = re.search(r"(\d+)", line)
    if m:
        p = int(m.group(1))
        if p not in pages:
            pages.append(p)

doc = fitz.open(str(PDF))
rendered = 0

for p in pages:
    out = OUT / f"page_{p:04d}.jpg"
    if out.exists():
        continue

    idx = p - 1
    if idx < 0 or idx >= len(doc):
        print("out of range:", p)
        continue

    page = doc[idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    pix.save(str(out))
    print("rendered:", out)
    rendered += 1

doc.close()
print("rendered missing pages:", rendered)
