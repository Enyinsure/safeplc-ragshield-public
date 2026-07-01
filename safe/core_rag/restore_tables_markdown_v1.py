import json
import re
from html import unescape
from pathlib import Path
from html.parser import HTMLParser

IN = Path.home() / "s7_table_stitch_output_v4_middle" / "stitched_tables.json"
OUT_MD = Path.home() / "s7_table_stitch_output_v4_middle" / "stitched_tables_restored.md"
OUT_JSON = Path.home() / "s7_table_stitch_output_v4_middle" / "stitched_tables_restored.json"
OUT_REPORT = Path.home() / "s7_table_stitch_output_v4_middle" / "table_markdown_report.txt"


class TableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = None
        self.current_row = None
        self.current_cell = None
        self.in_cell = False
        self.cell_attrs = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        tag = tag.lower()

        if tag == "table":
            self.current_table = []

        elif tag == "tr" and self.current_table is not None:
            self.current_row = []

        elif tag in ("td", "th") and self.current_row is not None:
            self.in_cell = True
            self.current_cell = ""
            self.cell_attrs = attrs

        elif tag == "img" and self.in_cell:
            self.current_cell += "[图标]"

    def handle_data(self, data):
        if self.in_cell and self.current_cell is not None:
            self.current_cell += data

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in ("td", "th") and self.in_cell:
            text = clean_cell(self.current_cell)
            colspan = int(self.cell_attrs.get("colspan", "1") or 1)
            rowspan = int(self.cell_attrs.get("rowspan", "1") or 1)
            self.current_row.append({
                "text": text,
                "colspan": colspan,
                "rowspan": rowspan,
            })
            self.in_cell = False
            self.current_cell = None
            self.cell_attrs = {}

        elif tag == "tr" and self.current_row is not None:
            self.current_table.append(self.current_row)
            self.current_row = None

        elif tag == "table" and self.current_table is not None:
            self.tables.append(self.current_table)
            self.current_table = None


def clean_cell(s: str) -> str:
    s = unescape(s or "")
    s = re.sub(r"\s+", " ", s)
    s = s.replace("|", "｜")
    return s.strip()


def parse_tables(html: str):
    parser = TableHTMLParser()
    parser.feed(html)
    return parser.tables


def expand_row(row):
    out = []
    for cell in row:
        text = cell["text"]
        colspan = max(1, int(cell.get("colspan", 1)))
        out.append(text)
        for _ in range(colspan - 1):
            out.append("")
    return out


def table_to_markdown(table):
    rows = [expand_row(r) for r in table]
    if not rows:
        return ""

    max_cols = max(len(r) for r in rows)
    norm = []
    for r in rows:
        r = r + [""] * (max_cols - len(r))
        norm.append(r)

    # 如果第一行像表头，用第一行做 header；否则生成通用列名
    header = norm[0]
    if not any(header):
        header = [f"列{i+1}" for i in range(max_cols)]
        body = norm
    else:
        body = norm[1:]

    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    for r in body:
        lines.append("| " + " | ".join(r) + " |")

    return "\n".join(lines)


def main():
    data = json.loads(IN.read_text(encoding="utf-8"))

    restored = []
    md_parts = ["# Restored Stitched Tables\n"]
    report = []

    for item in data:
        if item.get("num_parts", 1) <= 1:
            continue

        table_id = item.get("id")
        pages = item.get("pages")
        raw = item.get("merged_text", "")

        tables = parse_tables(raw)
        md_tables = [table_to_markdown(t) for t in tables]
        md_tables = [x for x in md_tables if x.strip()]

        restored.append({
            "id": table_id,
            "pages": pages,
            "num_parts": item.get("num_parts"),
            "source_file": item.get("source_file"),
            "num_html_tables": len(tables),
            "markdown": "\n\n".join(md_tables),
            "reason": item.get("reason"),
            "score": item.get("score"),
        })

        md_parts.append(f"\n## {table_id}\n")
        md_parts.append(f"- pages: {pages}")
        md_parts.append(f"- num_parts: {item.get('num_parts')}")
        md_parts.append(f"- num_html_tables: {len(tables)}")
        md_parts.append(f"- reason: {item.get('reason')}")
        md_parts.append("")
        md_parts.append("\n\n".join(md_tables[:5]))
        if len(md_tables) > 5:
            md_parts.append("\n\n> 仅展示前 5 个 HTML table 转换结果。")

        report.append(
            f"{table_id} pages={pages} parts={item.get('num_parts')} "
            f"html_tables={len(tables)} score={item.get('score')}"
        )

    OUT_JSON.write_text(json.dumps(restored, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text("\n".join(md_parts), encoding="utf-8")
    OUT_REPORT.write_text("\n".join(report), encoding="utf-8")

    print("written:", OUT_MD)
    print("written:", OUT_JSON)
    print("written:", OUT_REPORT)
    print("restored groups:", len(restored))


if __name__ == "__main__":
    main()
