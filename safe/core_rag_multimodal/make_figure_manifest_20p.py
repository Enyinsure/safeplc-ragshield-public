import json
from pathlib import Path

HOME = Path.home()
AUTO = HOME / "mineru_ocr_test_20pages_stable/1500_manual_collection_zh-CHS_zh-CHS/auto"
OUT_DIR = HOME / "s7_multimodal_v1"
IMG_LIST = OUT_DIR / "images_20pages_list.txt"
MANIFEST = OUT_DIR / "figure_cards/figure_manifest_20pages.jsonl"
SAMPLE_DIR = OUT_DIR / "images/sample_20pages"

MANIFEST.parent.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

paths = []
with IMG_LIST.open("r", encoding="utf-8") as f:
    for line in f:
        p = line.strip()
        if p:
            paths.append(Path(p))

records = []
for i, p in enumerate(paths, 1):
    fig_id = f"fig20p_{i:04d}"
    rec = {
        "doc_id": "1500_manual_collection_zh-CHS",
        "figure_id": fig_id,
        "image_path": str(p),
        "image_name": p.name,
        "source": "mineru_20pages_stable",
        "page": None,
        "caption": "",
        "nearby_text": "",
        "needs_vlm": True
    }
    records.append(rec)

with MANIFEST.open("w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# 抽前 30 张做软链接，方便人工浏览
for rec in records[:30]:
    src = Path(rec["image_path"])
    dst = SAMPLE_DIR / f'{rec["figure_id"]}_{src.name}'
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    dst.symlink_to(src)

print(f"images: {len(records)}")
print(f"manifest: {MANIFEST}")
print(f"sample_dir: {SAMPLE_DIR}")
