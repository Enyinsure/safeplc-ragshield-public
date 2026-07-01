import subprocess
import sys
from pathlib import Path

ASK = Path.home() / "ask_s7_stable.py"
OUT = Path.home() / "s7_rag_processed" / "ask_s7_batch_output.txt"

DEFAULT_QUESTIONS = [
    "CPU 1511 工作存储器是多少？",
    "CPU 1511-1 PN 的装载存储器最大是多少？",
    "PS 60W 24/48/60VDC HF 电源电压允许范围是多少？",
    "ET 200MP 电源模块安装要求",
    "ET 200MP 电源模块接线要求",
    "PS 60W 24/48/60VDC HF 必须插在哪个插槽？",
    "如何在 STEP 7 中查看诊断信息？",
    "CPU 显示屏有哪些诊断功能？",
    "S7-1500 固件更新要求",
    "S7-1500 工作温度范围",
]

def run_question(q: str) -> str:
    r = subprocess.run(
        ["python", str(ASK), q],
        text=True,
        capture_output=True,
        timeout=180,
    )
    return (r.stdout or "") + ("\n" + r.stderr if r.stderr else "")

def main():
    questions = sys.argv[1:]
    if not questions:
        questions = DEFAULT_QUESTIONS

    parts = []
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q}")
        parts.append("=" * 100)
        parts.append(f"QUESTION {i}: {q}")
        parts.append("=" * 100)
        parts.append(run_question(q).strip())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n\n".join(parts), encoding="utf-8")
    print("written:", OUT)

if __name__ == "__main__":
    main()
