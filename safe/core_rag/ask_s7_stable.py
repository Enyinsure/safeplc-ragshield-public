import re
import subprocess
import sys
from pathlib import Path

SCRIPT = Path.home() / "query_s7_chroma_v3_stable.py"


def run_query(question: str) -> str:
    result = subprocess.run(
        ["python", str(SCRIPT), question],
        text=True,
        capture_output=True,
        timeout=180,
    )

    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    return output.strip()


def extract_block(text: str, title: str) -> str:
    pattern = (
        r"={20,}\n"
        + re.escape(title)
        + r"\n"
        r"={20,}\n"
        r"(.*?)(?=\n={20,}\n|$)"
    )
    m = re.search(pattern, text, flags=re.S)
    if not m:
        return ""
    return m.group(1).strip()


def clean_evidence(evidence: str, max_chars: int = 1800) -> str:
    evidence = evidence.strip()

    # 保留 page / section / 原文片段，但避免过长
    if len(evidence) <= max_chars:
        return evidence

    return evidence[:max_chars].rstrip() + "\n……（证据片段已截断）"


def main():
    if len(sys.argv) < 2:
        print('用法：python ~/ask_s7.py "你的问题"')
        sys.exit(1)

    question = " ".join(sys.argv[1:]).strip()

    raw = run_query(question)

    answer = extract_block(raw, "最终答案")
    evidence = extract_block(raw, "证据")

    page = ""
    section = ""

    m_page = re.search(r"^page:\s*(.+)$", evidence, flags=re.M)
    if m_page:
        page = m_page.group(1).strip()

    m_section = re.search(r"^section:\s*(.+)$", evidence, flags=re.M)
    if m_section:
        section = m_section.group(1).strip()

    # 去掉证据块开头的 page / section / 分隔线，保留正文
    evidence_body = re.sub(r"^page:.*?\n", "", evidence, flags=re.M)
    evidence_body = re.sub(r"^section:.*?\n", "", evidence_body, flags=re.M)
    evidence_body = re.sub(r"^-{10,}\n", "", evidence_body, flags=re.M).strip()

    print("\n问题")
    print("-" * 80)
    print(question)

    print("\n答案")
    print("-" * 80)
    print(answer if answer else "未能生成明确答案。")

    print("\n依据")
    print("-" * 80)
    if page:
        print(f"页码：{page}")
    if section:
        print(f"章节：{section}")

    print("\n关键证据")
    print("-" * 80)
    print(clean_evidence(evidence_body) if evidence_body else "未找到可展示的证据片段。")


if __name__ == "__main__":
    main()
