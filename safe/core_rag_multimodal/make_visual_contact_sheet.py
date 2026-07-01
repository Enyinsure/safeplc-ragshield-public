from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

HOME = Path.home()
IMG_DIR = HOME / "s7_multimodal_v1/images/visual_candidate_pages"
OUT_DIR = HOME / "s7_multimodal_v1/images/contact_sheets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

imgs = sorted(IMG_DIR.glob("page_*.jpg"))
if not imgs:
    raise SystemExit(f"no images found in {IMG_DIR}")

thumb_w, thumb_h = 300, 420
cols, rows = 4, 3
margin = 30
label_h = 40
sheet_w = cols * thumb_w + (cols + 1) * margin
sheet_h = rows * (thumb_h + label_h) + (rows + 1) * margin

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
except:
    font = ImageFont.load_default()

for batch_idx in range(math.ceil(len(imgs) / (cols * rows))):
    batch = imgs[batch_idx * cols * rows : (batch_idx + 1) * cols * rows]
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)

    for i, path in enumerate(batch):
        r, c = divmod(i, cols)
        x = margin + c * (thumb_w + margin)
        y = margin + r * (thumb_h + label_h + margin)

        im = Image.open(path).convert("RGB")
        im.thumbnail((thumb_w, thumb_h))
        canvas = Image.new("RGB", (thumb_w, thumb_h), "white")
        ox = (thumb_w - im.width) // 2
        oy = (thumb_h - im.height) // 2
        canvas.paste(im, (ox, oy))

        sheet.paste(canvas, (x, y))
        draw.text((x, y + thumb_h + 8), path.stem, fill="black", font=font)

    out = OUT_DIR / f"visual_contact_sheet_{batch_idx+1:02d}.jpg"
    sheet.save(out, quality=92)

print("input images:", len(imgs))
print("contact sheets:", OUT_DIR)
