import json
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
QUERY_V2 = HOME / "query_s7_chroma_v2.py"
CHUNKS = HOME / "s7_rag_processed/s7_chunks_v2.jsonl"

TECH_KEYWORDS = [
    "技术数据", "技术规范", "工作存储器", "装载存储器", "支持多少",
    "额定", "允许范围", "电压", "电流", "功率", "安装要求", "接线要求",
    "尺寸", "重量", "PROFINET", "I/O", "IO", "模块数量"
]

def run_v2(query):
    r = subprocess.run(
        ["python", str(QUERY_V2), query],
        text=True,
        capture_output=True,
        timeout=180,
    )
    return r.stdout + "\n" + r.stderr

def parse_top_pages(v2_text, topn=3):
    pages = []
    current_rank = None

    for line in v2_text.splitlines():
        m_rank = re.match(r"rank:\s*(\d+)", line.strip())
        if m_rank:
            current_rank = int(m_rank.group(1))

        m_page = re.match(r"page:\s*(\d+)", line.strip())
        if m_page and current_rank is not None and current_rank <= topn:
            pages.append(int(m_page.group(1)))

    dedup = []
    for p in pages:
        if p not in dedup:
            dedup.append(p)
    return dedup

def page_radius_for_query(query):
    if any(k.lower() in query.lower() for k in TECH_KEYWORDS):
        return 2
    return 1

def load_chunks_by_pages(pages):
    wanted = set(pages)
    rows = []

    with CHUNKS.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            md = obj.get("metadata", {})
            page_no = md.get("page_no")
            if page_no in wanted:
                rows.append(obj)

    rows.sort(key=lambda x: (
        x.get("metadata", {}).get("page_no") or 0,
        x.get("metadata", {}).get("chunk_index") or 0,
    ))
    return rows

def expand_pages(seed_pages, radius):
    pages = set()
    for p in seed_pages:
        for q in range(p - radius, p + radius + 1):
            if q > 0:
                pages.add(q)
    return sorted(pages)

def print_keyword_windows(query, rows):
    terms = []
    for t in re.split(r"[\s，。？?、/()（）]+", query):
        t = t.strip()
        if len(t) >= 2:
            terms.append(t)

    # 手动增强一些常见同义字段
    if "工作存储器" in query:
        terms.extend(["工作存储器", "集成（用于程序）", "集成（用于数据）", "装载存储器"])
    if "I/O" in query or "IO" in query or "模块" in query:
        terms.extend(["I/O 模块", "IO 设备", "模块数量", "元素数量"])
    if "安装" in query:
        terms.extend(["安装", "装配", "安装导轨", "控制柜", "间距"])
    if "接线" in query:
        terms.extend(["接线", "端子", "L+", "M", "电源连接"])

    seen = set()
    print("\n" + "#" * 100)
    print("关键词窗口 / candidate evidence")
    print("#" * 100)

    found = False
    for obj in rows:
        text = obj.get("text", "")
        md = obj.get("metadata", {})
        for term in terms:
            pos = text.find(term)
            if pos < 0:
                continue

            key = (obj.get("id"), term)
            if key in seen:
                continue
            seen.add(key)

            start = max(0, pos - 350)
            end = min(len(text), pos + 900)
            print("\n" + "=" * 80)
            print("page:", md.get("page_no"))
            print("chunk:", obj.get("id"))
            print("section:", md.get("section"))
            print("matched:", term)
            print("-" * 80)
            print(text[start:end])
            found = True
            break

    if not found:
        print("未找到明显关键词窗口；请查看下方扩展上下文。")

def main():
    if len(sys.argv) < 2:
        print('用法: python ~/query_s7_chroma_v3_expand.py "你的问题"')
        sys.exit(1)

    query = " ".join(sys.argv[1:]).strip()

    print("query:", query)
    print("running v2 retrieval...")
    v2_text = run_v2(query)

    print("\n" + "#" * 100)
    print("V2 原始检索结果")
    print("#" * 100)
    print(v2_text)

    seed_pages = parse_top_pages(v2_text, topn=3)
    radius = page_radius_for_query(query)
    expanded_pages = expand_pages(seed_pages, radius)

    print("\n" + "#" * 100)
    print("V3 扩展策略")
    print("#" * 100)
    print("seed_pages:", seed_pages)
    print("radius:", radius)
    print("expanded_pages:", expanded_pages)

    rows = load_chunks_by_pages(expanded_pages)
    print("expanded_chunks:", len(rows))

    print_keyword_windows(query, rows)

    print("\n" + "#" * 100)
    print("扩展上下文 / expanded context")
    print("#" * 100)

    for obj in rows:
        md = obj.get("metadata", {})
        print("\n" + "=" * 100)
        print("page:", md.get("page_no"))
        print("chunk:", obj.get("id"))
        print("section:", md.get("section"))
        print("-" * 100)
        print(obj.get("text", "")[:2500])

if __name__ == "__main__":
    main()
