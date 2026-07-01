#!/usr/bin/env bash
set -e

cd ~

if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate s7rag
fi

python - <<'PY'
from pathlib import Path
import csv
import subprocess
import sys
from datetime import datetime

root = Path("~").expanduser()
report = root / "agent_v2_acceptance_report.md"
questions = root / "s7_agent_v2_questions.tsv"
script = root / "s7_multimodal_v1" / "ask_s7_agent_v2.py"

lines = []
lines.append("# S7 多模态 RAG Agent v2 多轮澄清验收报告")
lines.append("")
lines.append("## 测试时间")
lines.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
lines.append("")
lines.append("## 测试入口")
lines.append("")
lines.append(f"`{script}`")
lines.append("")
lines.append("## 测试目标")
lines.append("")
lines.append("Agent v2 在 Agent v1 + Safety Guard v1 之上增加多轮澄清、自动追问、上下文补充后继续执行能力。")
lines.append("")
lines.append("## 测试结果")
lines.append("")

with questions.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for i, row in enumerate(reader, start=1):
        q = (row.get("问题") or "").strip()
        ctx = (row.get("补充上下文") or "").strip()
        expected = (row.get("预期") or "").strip()

        if not q:
            continue

        cmd = [sys.executable, str(script), q]
        if ctx:
            cmd.extend(["--context", ctx])

        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
        )

        output = proc.stdout or ""
        err = proc.stderr or ""

        lines.append(f"### {i}. {q}")
        lines.append("")
        lines.append(f"- 补充上下文：{ctx if ctx else '无'}")
        lines.append(f"- 预期：{expected if expected else '无'}")
        lines.append(f"- 返回码：{proc.returncode}")
        lines.append("")
        lines.append("```text")
        lines.append(output.rstrip())
        if err.strip():
            lines.append("")
            lines.append("[stderr]")
            lines.append(err.rstrip())
        lines.append("```")
        lines.append("")

lines.append("## 人工验收标准")
lines.append("")
lines.append("- 缺少型号 / 订货号 / 模块名称的参数类问题，应显示“需要澄清”，并停止自动检索。")
lines.append("- 用户补充上下文后，应生成增强后问题并继续调用 Agent v1。")
lines.append("- 高风险问题应继续由 Safety Guard v1 输出完整拒答。")
lines.append("- PROFINET / HMI / EMC 等已具备通用证据的问题，不应被过度追问。")
lines.append("- Agent v2 不应绕过 Agent v1 和 Safety Guard v1。")
lines.append("- Streamlit v2 前端应支持问题输入、补充上下文输入和运行输出展示。")
lines.append("")
lines.append("## 结论")
lines.append("")
lines.append("待人工复核。")
lines.append("")

report.write_text("\n".join(lines), encoding="utf-8")
print(f"[OK] Agent v2 验收报告已生成：{report}")
PY
