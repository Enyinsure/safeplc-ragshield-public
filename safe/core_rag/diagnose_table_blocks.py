import json
from pathlib import Path

P = Path.home() / "s7_table_stitch_output_v2" / "stitched_tables.json"
OUT = Path.home() / "s7_table_stitch_output_v2" / "table_blocks_diagnosis.txt"

data = json.loads(P.read_text(encoding="utf-8"))

blocks = []
for item in data:
    for part in item.get("parts", []):
        blocks.append(part)

blocks.sort(key=lambda x: (
    x.get("source_file", ""),
    x.get("page_no") or 0,
    x.get("block_index") or 0,
))

lines = []
lines.append(f"total_blocks={len(blocks)}")
lines.append("")

for b in blocks:
    text = (b.get("text") or "").replace("\n", " ")
    text = text[:180]
    lines.append(
        f"page={b.get('page_no')} "
        f"idx={b.get('block_index')} "
        f"type={b.get('block_type')} "
        f"cols={b.get('col_count')} "
        f"rows={b.get('row_count')} "
        f"continued={b.get('continued_marker')} "
        f"bbox={b.get('bbox')} "
        f"source={Path(b.get('source_file','')).name}"
    )
    if b.get("section_hint"):
        lines.append(f"  section={b.get('section_hint')}")
    lines.append(f"  text={text}")
    lines.append("")

# 找相邻页、列数相同/相近的潜在跨页候选
lines.append("=" * 100)
lines.append("ADJACENT CANDIDATES")
lines.append("=" * 100)

for a, b in zip(blocks, blocks[1:]):
    if a.get("source_file") != b.get("source_file"):
        continue

    pa = a.get("page_no")
    pb = b.get("page_no")
    ca = a.get("col_count") or 0
    cb = b.get("col_count") or 0

    if pb == pa + 1 and ca > 0 and cb > 0 and abs(ca - cb) <= 1:
        lines.append(
            f"candidate pages={pa}->{pb} "
            f"cols={ca}->{cb} "
            f"type={a.get('block_type')}->{b.get('block_type')} "
            f"continued={a.get('continued_marker')}->{b.get('continued_marker')} "
            f"source={Path(a.get('source_file','')).name}"
        )
        ta = (a.get("text") or "").replace("\n", " ")[:160]
        tb = (b.get("text") or "").replace("\n", " ")[:160]
        lines.append(f"  A: {ta}")
        lines.append(f"  B: {tb}")
        lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("written:", OUT)
