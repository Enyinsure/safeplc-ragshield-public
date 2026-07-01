import json
import re
from pathlib import Path

HOME = Path.home()
IN_PAGES = HOME / "s7_full_pages.jsonl"

OUT_DIR = HOME / "s7_rag_processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PAGES = OUT_DIR / "s7_pages_clean.jsonl"
OUT_CHUNKS = OUT_DIR / "s7_chunks_v2.jsonl"
REPORT = OUT_DIR / "clean_report.txt"

MAX_CHARS = 1200
OVERLAP_CHARS = 180
MIN_CHARS = 40

NOISE_PATTERNS = [
    ("copyright", re.compile(r"^©\s*Siemens\s+AG\s+\d{4}\s*-\s*\d{4}.*$", re.I)),
    ("a5e_code", re.compile(r"^A5E\d+[A-Z0-9-]*(?:,\s*\d{2}/\d{4})?$", re.I)),
    ("support_domain", re.compile(r"^support\.industry\.siemens\.com$", re.I)),
    ("simatic_single", re.compile(r"^SIMATIC$", re.I)),
    ("system_manual", re.compile(r"^(系统手册|功能手册|设备手册|操作说明|原始操作说明)$")),
    ("manual_collection_en", re.compile(r"^Manual Collection$", re.I)),
    ("version_single", re.compile(r"^版本$")),
]

def is_noise_line(line, idx, lines):
    s = line.strip()
    if not s:
        return True, "empty"

    for name, pat in NOISE_PATTERNS:
        if pat.match(s):
            return True, name

    # 页码通常出现在页眉/页脚附近，或夹在版权信息旁边。
    if re.match(r"^\d{1,5}$", s):
        near_edge = idx <= 2 or idx >= len(lines) - 3
        prev_line = lines[idx - 1].strip() if idx > 0 else ""
        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
        near_footer = (
            "Siemens AG" in prev_line
            or "Siemens AG" in next_line
            or prev_line.startswith("A5E")
            or next_line.startswith("A5E")
            or prev_line == "SIMATIC"
            or next_line == "SIMATIC"
        )
        if near_edge or near_footer:
            return True, "page_number"

    return False, ""

def normalize_text(text):
    raw_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    kept = []
    dropped = {}

    for i, line in enumerate(raw_lines):
        line = line.strip()
        drop, reason = is_noise_line(line, i, raw_lines)
        if drop:
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        kept.append(line)

    # 合并过多空白，但保留基本换行结构
    cleaned_lines = []
    prev_blank = False
    for line in kept:
        line = re.sub(r"[ \t]+", " ", line).strip()
        if not line:
            if not prev_blank:
                cleaned_lines.append("")
            prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), dropped

def split_long_text(text, max_chars=MAX_CHARS, overlap=OVERLAP_CHARS):
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if len(text) >= MIN_CHARS else []

    # 优先按段落切
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks = []
    buf = ""

    def flush_buf():
        nonlocal buf
        if buf.strip():
            chunks.extend(slice_if_needed(buf.strip(), max_chars, overlap))
        buf = ""

    for para in paras:
        if not buf:
            buf = para
        elif len(buf) + 2 + len(para) <= max_chars:
            buf += "\n\n" + para
        else:
            flush_buf()
            buf = para
    flush_buf()

    final = []
    for c in chunks:
        if len(c.strip()) >= MIN_CHARS:
            final.append(c.strip())
    return final

def slice_if_needed(text, max_chars, overlap):
    if len(text) <= max_chars:
        return [text]

    pieces = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)

        # 尽量在句号/分号/换行附近断开
        if end < n:
            window = text[start:end]
            cut_candidates = [
                window.rfind("。"),
                window.rfind("；"),
                window.rfind("！"),
                window.rfind("？"),
                window.rfind("\n"),
            ]
            cut = max(cut_candidates)
            if cut > max_chars * 0.55:
                end = start + cut + 1

        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)

        if end >= n:
            break
        start = max(0, end - overlap)

    return pieces

def main():
    if not IN_PAGES.exists():
        raise FileNotFoundError(f"Missing input: {IN_PAGES}")

    total_pages = 0
    kept_pages = 0
    total_chunks = 0
    drop_counter = {}
    char_before = 0
    char_after = 0

    with IN_PAGES.open("r", encoding="utf-8") as fin, \
         OUT_PAGES.open("w", encoding="utf-8") as fpages, \
         OUT_CHUNKS.open("w", encoding="utf-8") as fchunks:

        for line in fin:
            if not line.strip():
                continue

            page = json.loads(line)
            total_pages += 1

            original_text = page.get("text", "") or ""
            char_before += len(original_text)

            clean_text, dropped = normalize_text(original_text)

            for k, v in dropped.items():
                drop_counter[k] = drop_counter.get(k, 0) + v

            if len(clean_text) < MIN_CHARS:
                continue

            char_after += len(clean_text)
            kept_pages += 1

            clean_page = dict(page)
            clean_page["text"] = clean_text
            clean_page["clean_version"] = "s7_clean_v2"
            fpages.write(json.dumps(clean_page, ensure_ascii=False) + "\n")

            chunks = split_long_text(clean_text)
            for ci, chunk_text in enumerate(chunks):
                chunk = {
                    "id": f"s7_v2_page_{page.get('page_no', total_pages)}_chunk_{ci}",
                    "text": chunk_text,
                    "metadata": {
                        "source": page.get("source", "S7-1500/ET 200MP Manual Collection"),
                        "pdf_path": page.get("pdf_path", ""),
                        "page_no": page.get("page_no"),
                        "page_index": page.get("page_index"),
                        "section": page.get("section", ""),
                        "chunk_index": ci,
                        "clean_version": "s7_clean_v2",
                        "chunk_chars": len(chunk_text),
                    },
                }
                fchunks.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_chunks += 1

    with REPORT.open("w", encoding="utf-8") as f:
        f.write(f"input_pages={total_pages}\n")
        f.write(f"kept_pages={kept_pages}\n")
        f.write(f"output_chunks={total_chunks}\n")
        f.write(f"chars_before={char_before}\n")
        f.write(f"chars_after={char_after}\n")
        f.write(f"char_reduction={char_before - char_after}\n")
        f.write("\ndropped_lines:\n")
        for k, v in sorted(drop_counter.items(), key=lambda x: x[0]):
            f.write(f"{k}={v}\n")

    print("DONE")
    print("pages:", OUT_PAGES)
    print("chunks:", OUT_CHUNKS)
    print("report:", REPORT)
    print("output_chunks:", total_chunks)

if __name__ == "__main__":
    main()
