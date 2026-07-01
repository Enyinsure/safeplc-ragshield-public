import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


TEXT_KEYS = [
    "text", "content", "markdown", "md", "html", "latex",
    "table_body", "table", "caption", "ocr_text"
]

TYPE_KEYS = [
    "type", "block_type", "category", "layout_type", "class", "label"
]

BBOX_KEYS = [
    "bbox", "box", "layout_bbox", "poly", "polygon"
]


@dataclass
class TableBlock:
    source_file: str
    page_no: int
    block_index: int
    block_type: str
    text: str
    bbox: Optional[List[float]]
    col_count: int
    row_count: int
    continued_marker: bool
    section_hint: str = ""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> List[Any]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def find_candidate_files(root: Path) -> List[Path]:
    names = []
    patterns = [
        "*content_list*.json",
        "*middle*.json",
        "*model*.json",
        "*layout*.json",
    ]

    skip_parts = {
        ".cache", ".conda", ".local", ".nv", "__pycache__",
        "s7_chroma_db", "s7_chroma_db_v2", "s7_chroma_db_v2_stable",
        "s7_chroma_db_v3",
    }

    for pat in patterns:
        for p in root.rglob(pat):
            if any(part in skip_parts for part in p.parts):
                continue
            low_name = p.name.lower()
            if any(x in low_name for x in ["pages.jsonl", "full_pages", "pages_clean", "chunks.jsonl", "full_chunks"]):
                continue
            if p.is_file():
                names.append(p)

    out = []
    seen = set()
    for p in names:
        if p not in seen:
            seen.add(p)
            out.append(p)

    return sorted(out, key=lambda x: str(x))


def get_block_type(obj: Dict[str, Any]) -> str:
    for k in TYPE_KEYS:
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def get_bbox(obj: Dict[str, Any]) -> Optional[List[float]]:
    for k in BBOX_KEYS:
        v = obj.get(k)
        if isinstance(v, list):
            flat = []
            for x in v:
                if isinstance(x, (int, float)):
                    flat.append(float(x))
                elif isinstance(x, list):
                    for y in x:
                        if isinstance(y, (int, float)):
                            flat.append(float(y))
            if len(flat) >= 4:
                return flat[:4]
    return None


def text_from_obj(obj: Dict[str, Any]) -> str:
    parts = []

    for k in TEXT_KEYS:
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())

    # MinerU 有些结构把 table 内容放在 res / table_res 里
    for k in ["res", "table_res", "extra", "metadata"]:
        v = obj.get(k)
        if isinstance(v, dict):
            for kk in TEXT_KEYS:
                vv = v.get(kk)
                if isinstance(vv, str) and vv.strip():
                    parts.append(vv.strip())

    # 去重但保序
    out = []
    seen = set()
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)

    return "\n".join(out).strip()


def normalize_text(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def has_continued_marker(text: str) -> bool:
    patterns = [
        r"\(continued\)",
        r"\[continued\]",
        r"continued",
        r"续表",
        r"接上页",
        r"下页继续",
        r"上一页继续",
        r"续",
    ]
    low = text.lower()
    return any(re.search(p, low, flags=re.I) for p in patterns)


def count_markdown_cols(text: str) -> int:
    counts = []
    for line in text.splitlines():
        line = line.strip()
        if line.count("|") >= 2:
            # 去掉首尾 pipe 后统计列
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 2:
                counts.append(len(cols))
    return max(counts) if counts else 0


def count_html_cols(text: str) -> int:
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S)
    counts = []
    for row in rows[:10]:
        n = len(re.findall(r"<t[dh][^>]*>", row, flags=re.I))
        if n:
            counts.append(n)
    return max(counts) if counts else 0


def guess_table_shape(text: str) -> Tuple[int, int]:
    text = normalize_text(text)
    if not text:
        return 0, 0

    md_cols = count_markdown_cols(text)
    html_cols = count_html_cols(text)

    col_count = max(md_cols, html_cols)

    if col_count == 0:
        # 对纯文本表格做粗略估计：多行短字段表，先给 2 列兜底
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        if len(lines) >= 6:
            numeric_like = sum(bool(re.search(r"\d|V|A|W|kbyte|Mbyte|Gbyte|°C|ms|ns", x)) for x in lines)
            if numeric_like >= 2:
                col_count = 2

    row_count = 0
    if "<tr" in text.lower():
        row_count = len(re.findall(r"<tr[^>]*>", text, flags=re.I))
    elif md_cols:
        row_count = sum(1 for line in text.splitlines() if line.count("|") >= 2)
    else:
        row_count = len([x for x in text.splitlines() if x.strip()])

    return col_count, row_count



def looks_like_table(block_type: str, text: str) -> bool:
    bt = block_type.lower()

    # 只接受明确表格块
    if any(k in bt for k in ["table", "表格", "tabular"]):
        return True

    # HTML 表格
    if "<table" in text.lower() and "</table>" in text.lower():
        return True

    # Markdown 表格
    if count_markdown_cols(text) >= 2:
        return True

    return False

def page_no_from_obj(obj: Dict[str, Any], page_hint: Optional[int]) -> Optional[int]:
    for k in ["page_no", "page", "page_num"]:
        v = obj.get(k)
        if isinstance(v, int):
            return v
        if isinstance(v, str) and v.isdigit():
            return int(v)

    for k in ["page_idx", "page_index"]:
        v = obj.get(k)
        if isinstance(v, int):
            return v + 1
        if isinstance(v, str) and v.isdigit():
            return int(v) + 1

    return page_hint


def collect_blocks_from_node(
    node: Any,
    source_file: str,
    blocks: List[TableBlock],
    page_hint: Optional[int] = None,
    counter: Optional[List[int]] = None,
):
    if counter is None:
        counter = [0]

    if isinstance(node, list):
        # 顶层 list 很可能是按页组织；如果元素没有 page 信息，用 index+1
        for i, item in enumerate(node):
            next_hint = page_hint
            if page_hint is None and isinstance(item, (dict, list)):
                next_hint = i + 1
            collect_blocks_from_node(item, source_file, blocks, next_hint, counter)
        return

    if not isinstance(node, dict):
        return

    page_no = page_no_from_obj(node, page_hint)
    block_type = get_block_type(node)
    text = normalize_text(text_from_obj(node))
    bbox = get_bbox(node)

    if page_no is not None and text and looks_like_table(block_type, text):
        col_count, row_count = guess_table_shape(text)
        blocks.append(
            TableBlock(
                source_file=source_file,
                page_no=int(page_no),
                block_index=counter[0],
                block_type=block_type or "unknown",
                text=text,
                bbox=bbox,
                col_count=col_count,
                row_count=row_count,
                continued_marker=has_continued_marker(text),
                section_hint=str(node.get("section", "") or node.get("title", "") or ""),
            )
        )
        counter[0] += 1

    # 递归遍历子结构
    for v in node.values():
        if isinstance(v, (dict, list)):
            collect_blocks_from_node(v, source_file, blocks, page_no, counter)


def collect_from_file(path: Path) -> List[TableBlock]:
    blocks: List[TableBlock] = []

    try:
        if path.suffix.lower() == ".jsonl":
            data = read_jsonl(path)
        else:
            data = read_json(path)
    except Exception as e:
        print(f"[WARN] failed to read {path}: {e}")
        return blocks

    collect_blocks_from_node(data, str(path), blocks)
    return blocks


def bbox_y(bbox: Optional[List[float]]) -> Optional[float]:
    if not bbox or len(bbox) < 4:
        return None
    return min(bbox[1], bbox[3])


def sort_blocks(blocks: List[TableBlock]) -> List[TableBlock]:
    return sorted(
        blocks,
        key=lambda b: (
            b.source_file,
            b.page_no,
            999999 if bbox_y(b.bbox) is None else bbox_y(b.bbox),
            b.block_index,
        ),
    )



def html_cells_first_row(text: str) -> List[str]:
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.I | re.S)
    if not rows:
        return []
    row = rows[0]
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.I | re.S)
    out = []
    for c in cells:
        c = re.sub(r"<[^>]+>", "", c)
        c = re.sub(r"&quot;|&nbsp;|&#160;", " ", c)
        c = re.sub(r"\s+", "", c)
        if c:
            out.append(c)
    return out

def header_similarity(a: TableBlock, b: TableBlock) -> bool:
    ha = html_cells_first_row(a.text)
    hb = html_cells_first_row(b.text)
    if not ha or not hb:
        return False
    sa = set(ha)
    sb = set(hb)
    if not sa or not sb:
        return False
    overlap = len(sa & sb)
    return overlap >= 2 or overlap >= min(len(sa), len(sb))

def bbox_continuation_like(a: TableBlock, b: TableBlock) -> bool:
    if not a.bbox or not b.bbox:
        return False
    # bbox = [x0, y0, x1, y1]，MinerU 坐标下页面高度约 750 左右
    ay1 = max(a.bbox[1], a.bbox[3])
    by0 = min(b.bbox[1], b.bbox[3])
    # 前一页表格靠近页底，后一页表格靠近页顶
    return ay1 >= 650 and by0 <= 180

def dedup_blocks(blocks: List[TableBlock]) -> List[TableBlock]:
    out = []
    seen = set()
    for b in blocks:
        bbox_key = None
        if b.bbox:
            bbox_key = tuple(round(x, 1) for x in b.bbox)
        text_key = re.sub(r"\s+", "", b.text)[:500]
        key = (b.source_file, b.page_no, b.col_count, b.row_count, bbox_key, text_key)
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


def same_columns(a: TableBlock, b: TableBlock) -> bool:
    if a.col_count <= 0 or b.col_count <= 0:
        return False
    return abs(a.col_count - b.col_count) <= 1




def is_consecutive_candidate(a: TableBlock, b: TableBlock) -> Tuple[bool, str, int]:
    if a.source_file != b.source_file:
        return False, "", 0

    if b.page_no != a.page_no + 1:
        return False, "", 0

    if not same_columns(a, b):
        return False, "", 0

    score = 0
    reasons = []

    if a.continued_marker or b.continued_marker:
        score += 50
        reasons.append("continued_marker")

    if a.section_hint and b.section_hint and a.section_hint == b.section_hint:
        score += 30
        reasons.append("same_section")

    if header_similarity(a, b):
        score += 45
        reasons.append("same_header")

    if bbox_continuation_like(a, b):
        score += 35
        reasons.append("bbox_bottom_to_top")

    if "table" in a.block_type.lower() and "table" in b.block_type.lower():
        score += 15
        reasons.append("both_table_type")

    # 两个相邻 HTML table，列数相同，且表头相同或 bbox 呈跨页形态，则合并
    return score >= 45, "+".join(reasons), score

def stitch_blocks(blocks: List[TableBlock]) -> List[Dict[str, Any]]:
    blocks = dedup_blocks(blocks)
    blocks = sort_blocks(blocks)
    groups: List[List[TableBlock]] = []
    MAX_GROUP_PARTS = 8

    used = set()
    for i, b in enumerate(blocks):
        if i in used:
            continue

        group = [b]
        used.add(i)

        current = b
        changed = True

        while changed and len(group) < MAX_GROUP_PARTS:
            changed = False
            best_j = None
            best_score = -1
            best_reason = ""

            for j, cand in enumerate(blocks):
                if j in used:
                    continue
                ok, reason, score = is_consecutive_candidate(current, cand)
                if ok and score > best_score:
                    best_j = j
                    best_score = score
                    best_reason = reason

            if best_j is not None:
                cand = blocks[best_j]
                group.append(cand)
                used.add(best_j)
                current = cand
                changed = True

        groups.append(group)

    stitched = []
    for gi, g in enumerate(groups):
        pages = [x.page_no for x in g]
        if len(g) == 1:
            reason = "single_table"
            score = 0
        else:
            reason_items = []
            score = 0
            for a, b in zip(g, g[1:]):
                _, r, sc = is_consecutive_candidate(a, b)
                reason_items.append(r)
                score += sc
            reason = ";".join(reason_items)

        merged_text = merge_table_texts([x.text for x in g])

        stitched.append({
            "id": f"stitched_table_{gi:04d}",
            "source_file": g[0].source_file,
            "pages": pages,
            "num_parts": len(g),
            "reason": reason,
            "score": score,
            "col_counts": [x.col_count for x in g],
            "row_counts": [x.row_count for x in g],
            "section_hints": [x.section_hint for x in g if x.section_hint],
            "merged_text": merged_text,
            "parts": [asdict(x) for x in g],
        })

    return stitched

def merge_table_texts(texts: List[str]) -> str:
    # 简单合并：如果是 Markdown 表格，尽量去掉后续重复表头分隔线
    merged = []
    seen_header = False

    for idx, text in enumerate(texts):
        lines = text.splitlines()

        if idx == 0:
            merged.extend(lines)
            if any("|" in x for x in lines[:3]):
                seen_header = True
            continue

        cleaned = []
        for line in lines:
            s = line.strip()
            if seen_header and re.match(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", s):
                continue
            # 去掉常见续表标记
            if re.search(r"continued|续表|接上页|下页继续", s, flags=re.I):
                continue
            cleaned.append(line)

        merged.append("")
        merged.extend(cleaned)

    return "\n".join(merged).strip()



def page_overlap_ratio(a_pages, b_pages):
    a = set(a_pages)
    b = set(b_pages)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))

def filter_overlapping_groups(stitched: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # 多页组优先：分数高、页数长、part 多
    multi = [x for x in stitched if x.get("num_parts", 1) > 1]
    single = [x for x in stitched if x.get("num_parts", 1) <= 1]

    multi_sorted = sorted(
        multi,
        key=lambda x: (
            -int(x.get("score", 0)),
            -len(x.get("pages", [])),
            -int(x.get("num_parts", 0)),
        )
    )

    kept = []
    for item in multi_sorted:
        pages = item.get("pages", [])
        source = item.get("source_file", "")

        conflict = False
        for old in kept:
            if old.get("source_file", "") != source:
                continue
            # 如果页码高度重叠，认为是重复/派生合并组，只保留前面高分组
            if page_overlap_ratio(pages, old.get("pages", [])) >= 0.5:
                conflict = True
                break

        if not conflict:
            kept.append(item)

    # 单页表如果落在已保留跨页表中，就不再输出，避免重复
    final = kept[:]
    for item in single:
        pages = set(item.get("pages", []))
        source = item.get("source_file", "")
        covered = False
        for old in kept:
            if old.get("source_file", "") == source and pages <= set(old.get("pages", [])):
                covered = True
                break
        if not covered:
            final.append(item)

    final = sorted(
        final,
        key=lambda x: (
            x.get("source_file", ""),
            min(x.get("pages", [0])),
            x.get("id", ""),
        )
    )

    # 重新编号
    for i, item in enumerate(final):
        item["id"] = f"stitched_table_{i:04d}"

    return final


def write_outputs(stitched: List[Dict[str, Any]], outdir: Path):
    stitched = filter_overlapping_groups(stitched)
    outdir.mkdir(parents=True, exist_ok=True)

    json_path = outdir / "stitched_tables.json"
    md_path = outdir / "stitched.md"
    report_path = outdir / "stitch_report.txt"

    json_path.write_text(json.dumps(stitched, ensure_ascii=False, indent=2), encoding="utf-8")

    md_parts = ["# Stitched Tables\n"]
    for item in stitched:
        if item["num_parts"] <= 1:
            continue
        md_parts.append(f"\n## {item['id']}\n")
        md_parts.append(f"- source: `{item['source_file']}`")
        md_parts.append(f"- pages: {item['pages']}")
        md_parts.append(f"- reason: {item['reason']}")
        md_parts.append(f"- score: {item['score']}")
        md_parts.append("\n```text")
        md_parts.append(item["merged_text"][:6000])
        if len(item["merged_text"]) > 6000:
            md_parts.append("\n... truncated ...")
        md_parts.append("```\n")

    md_path.write_text("\n".join(md_parts), encoding="utf-8")

    total = len(stitched)
    multi = sum(1 for x in stitched if x["num_parts"] > 1)
    report = [
        f"total_table_groups={total}",
        f"multi_page_groups={multi}",
        f"single_table_groups={total - multi}",
        "",
        "top_multi_page_groups:",
    ]

    for item in sorted([x for x in stitched if x["num_parts"] > 1], key=lambda x: -x["score"])[:30]:
        report.append(
            f"{item['id']} pages={item['pages']} parts={item['num_parts']} "
            f"score={item['score']} reason={item['reason']} source={item['source_file']}"
        )

    report_path.write_text("\n".join(report), encoding="utf-8")

    print("DONE")
    print("json:", json_path)
    print("md:", md_path)
    print("report:", report_path)
    print(f"total groups: {total}")
    print(f"multi-page groups: {multi}")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path.home()), help="search root")
    parser.add_argument("--outdir", default=str(Path.home() / "s7_table_stitch_output"))
    parser.add_argument("--file", action="append", default=[], help="specific json/jsonl file; can repeat")
    args = parser.parse_args()

    if args.file:
        files = [Path(x).expanduser() for x in args.file]
    else:
        files = find_candidate_files(Path(args.root).expanduser())

    print("candidate files:")
    for p in files:
        print(" ", p)

    all_blocks = []
    for p in files:
        blocks = collect_from_file(p)
        if blocks:
            print(f"[OK] {p}: table-like blocks = {len(blocks)}")
            all_blocks.extend(blocks)

    print("total table-like blocks:", len(all_blocks))

    stitched = stitch_blocks(all_blocks)
    write_outputs(stitched, Path(args.outdir).expanduser())


if __name__ == "__main__":
    main()
