from pathlib import Path
import math
import fitz

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
label_h = 35

sheet_w = cols * thumb_w + (cols + 1) * margin
sheet_h = rows * (thumb_h + label_h) + (rows + 1) * margin

per_sheet = cols * rows
num_sheets = math.ceil(len(imgs) / per_sheet)

for batch_idx in range(num_sheets):
    batch = imgs[batch_idx * per_sheet : (batch_idx + 1) * per_sheet]

    doc = fitz.open()
    page = doc.new_page(width=sheet_w, height=sheet_h)

    for i, img_path in enumerate(batch):
        r, c = divmod(i, cols)
        x = margin + c * (thumb_w + margin)
        y = margin + r * (thumb_h + label_h + margin)

        rect = fitz.Rect(x, y, x + thumb_w, y + thumb_h)
        page.insert_image(rect, filename=str(img_path), keep_proportion=True)

        page.insert_text(
            fitz.Point(x, y + thumb_h + 22),
            img_path.stem,
            fontsize=16,
            color=(0, 0, 0),
        )

    pdf_out = OUT_DIR / f"visual_contact_sheet_{batch_idx+1:02d}.pdf"
    jpg_out = OUT_DIR / f"visual_contact_sheet_{batch_idx+1:02d}.jpg"

    doc.save(str(pdf_out))
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    pix.save(str(jpg_out))
    doc.close()

print("input images:", len(imgs))
print("contact sheets:", OUT_DIR)
