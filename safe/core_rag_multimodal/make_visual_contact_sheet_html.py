from pathlib import Path
import html
import re

HOME = Path.home()
IMG_DIR = HOME / "s7_multimodal_v1/images/visual_candidate_pages"
OUT_DIR = HOME / "s7_multimodal_v1/images/contact_sheets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

imgs = sorted(IMG_DIR.glob("page_*.jpg"))

if not imgs:
    raise SystemExit(f"no images found in {IMG_DIR}")

cards = []
for p in imgs:
    m = re.search(r"page_(\d+)", p.stem)
    page_no = m.group(1) if m else p.stem
    rel = p.relative_to(OUT_DIR)
    cards.append(f"""
    <div class="card">
      <a href="{html.escape(str(rel))}" target="_blank">
        <img src="{html.escape(str(rel))}" loading="lazy">
      </a>
      <div class="label">page_{page_no}</div>
    </div>
    """)

out = OUT_DIR / "visual_contact_sheet.html"

out.write_text(f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>S7 Visual Candidate Pages</title>
<style>
body {{
  font-family: Arial, sans-serif;
  margin: 20px;
  background: #f7f7f7;
}}
h1 {{
  font-size: 22px;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}}
.card {{
  background: white;
  border: 1px solid #ddd;
  padding: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}}
.card img {{
  width: 100%;
  height: 360px;
  object-fit: contain;
  background: white;
  border: 1px solid #eee;
}}
.label {{
  margin-top: 8px;
  font-size: 16px;
  font-weight: bold;
  color: #222;
}}
.note {{
  margin-bottom: 20px;
  color: #555;
}}
</style>
</head>
<body>
<h1>S7-1500 / ET 200MP 视觉候选页总览</h1>
<div class="note">
点击缩略图可打开原始整页图。请记录真正包含硬件图、接口图、端子图、接线图、拓扑图的 page 编号。
</div>
<div class="grid">
{''.join(cards)}
</div>
</body>
</html>
""", encoding="utf-8")

print("images:", len(imgs))
print("html:", out)
