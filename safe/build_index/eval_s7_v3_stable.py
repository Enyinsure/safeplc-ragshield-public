import subprocess
from pathlib import Path

QUERIES = [
    "CPU 1511 工作存储器是多少？",
    "CPU 1511-1 PN 的装载存储器最大是多少？",
    "CPU 1511-1 PN 的电源电压允许范围是多少？",
    "CPU 1511 支持多少 I/O 模块？",
    "PS 60W 24/48/60VDC HF 电源电压允许范围是多少？",
    "ET 200MP 电源模块安装要求",
    "ET 200MP 电源模块接线要求",
    "PS 60W 24/48/60VDC HF 安装要求",
    "PS 60W 24/48/60VDC HF 接线要求",
    "S7-1500 24V DC 电源接线要求",
    "S7-1500 PROFINET 诊断方法",
    "如何在 STEP 7 中查看诊断信息？",
    "CPU 显示屏有哪些诊断功能？",
    "S7-1500 安全功能超低电压 SELV PELV 要求",
    "S7-1500 防护等级 IP20 是什么意思？",
    "I&M 数据支持到 I&M 几？",
    "S7-1500 固件更新要求",
    "模块电气隔离测试电压是多少？",
    "S7-1500 工作温度范围",
    "PS 60W 24/48/60VDC HF 必须插在哪个插槽？",
]

OUT = Path.home() / "s7_rag_processed" / "eval_s7_v3.txt"
SCRIPT = Path.home() / "query_s7_chroma_v3.py"

def run(q):
    r = subprocess.run(
        ["python", str(SCRIPT), q],
        text=True,
        capture_output=True,
        timeout=180,
    )
    return r.stdout + "\n" + r.stderr

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    parts = []
    for i, q in enumerate(QUERIES, 1):
        print(f"[{i}/{len(QUERIES)}] {q}")
        parts.append("=" * 100)
        parts.append(f"QUERY {i}: {q}")
        parts.append("=" * 100)
        parts.append(run(q))

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print("written:", OUT)

if __name__ == "__main__":
    main()
