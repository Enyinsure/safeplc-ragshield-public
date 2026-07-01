#!/usr/bin/env bash
set -e

cd ~

PKG=S7_MULTIMODAL_RAG_V1_AGENT_V2.tar.gz
SHA=S7_MULTIMODAL_RAG_V1_AGENT_V2.sha256
OUTDIR=release_selfcheck_agent_v2
REPORT=release_selfcheck_agent_v2_report.md

{
  echo "# S7 Agent v2 交付包解包自检报告"
  echo
  echo "## 测试时间"
  date
  echo
} > "$REPORT"

echo "[1/7] 检查交付包和 sha256 文件"
{
  echo "## 1. 文件存在性检查"
  echo
  ls -lh "$PKG" "$SHA"
  echo
} >> "$REPORT"

echo "[2/7] 校验 sha256"
{
  echo "## 2. sha256 校验"
  echo
  echo '```text'
  sha256sum -c "$SHA"
  echo '```'
  echo
} >> "$REPORT"

echo "[3/7] 解包到自检目录"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
tar -xzf "$PKG" -C "$OUTDIR"

{
  echo "## 3. 解包目录"
  echo
  echo "\`~/$OUTDIR\`"
  echo
} >> "$REPORT"

echo "[4/7] 检查核心文件"
{
  echo "## 4. 核心文件检查"
  echo
  echo '```text'
  ls -lh \
    "$OUTDIR/s7_multimodal_v1/agent_clarifier_v2.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v2.py" \
    "$OUTDIR/s7_multimodal_v1/app_streamlit_agent_v2.py" \
    "$OUTDIR/s7_multimodal_v1/agent_planner_v1.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v1.py" \
    "$OUTDIR/s7_multimodal_v1/safety_guard_v1.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_multimodal_final_safety.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_multimodal_final.py" \
    "$OUTDIR/s7_multimodal_v1/index/chroma_figures_v1/chroma.sqlite3" \
    "$OUTDIR/s7_multimodal_v1/images/visual_candidate_pages/page_2478.jpg" \
    "$OUTDIR/s7_multimodal_v1/images/visual_candidate_pages/page_0641.jpg" \
    "$OUTDIR/run_streamlit_s7_rag_agent_v2.sh" \
    "$OUTDIR/run_agent_v2_acceptance.sh" \
    "$OUTDIR/agent_v2_acceptance_report.md" \
    "$OUTDIR/PROJECT_FINAL_STATUS_AGENT_V2.txt"
  echo '```'
  echo
} >> "$REPORT"

echo "[5/7] 测试 Agent v2 澄清层"
{
  echo "## 5. Agent v2 澄清层快速测试"
  echo
  echo '```text'
  cd "${HOME}/${OUTDIR}/s7_multimodal_v1"
  python - <<'PY'
from agent_clarifier_v2 import make_clarification_decision

tests = [
    ("某个模块的电源电压允许范围是多少", ""),
    ("某个模块的电源电压允许范围是多少", "PS 60W 24/48/60VDC HF"),
    ("PROFINET 环网如何连接 HMI 设备", ""),
    ("能不能带电接 24V 电源端子", ""),
    ("EMC 要求是什么", ""),
]

for q, ctx in tests:
    d = make_clarification_decision(q, ctx)
    print(q)
    print("  context:", ctx if ctx else "无")
    print("  enhanced:", d.enhanced_question)
    print("  clarify:", d.needs_clarification)
    print("  execute:", d.can_execute)
    print("  safety:", d.safety_level)
PY
  echo '```'
  echo
} >> "${HOME}/${REPORT}"

cd ~

echo "[6/7] 测试 Agent v2 命令行入口"
{
  echo "## 6. Agent v2 命令行入口快速测试"
  echo
  echo '```text'
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v2.py" "某个模块的电源电压允许范围是多少"
  echo
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v2.py" "某个模块的电源电压允许范围是多少" --context "PS 60W 24/48/60VDC HF"
  echo
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v2.py" "能不能带电接 24V 电源端子"
  echo '```'
  echo
} >> "$REPORT"

echo "[7/7] 记录包清单摘要"
{
  echo "## 7. 包清单摘要"
  echo
  echo '```text'
  tar -tzf "$PKG" | head -120
  echo '```'
  echo
  echo "## 结论"
  echo
  echo "待人工复核。"
} >> "$REPORT"

echo "[OK] Agent v2 自检完成：~/$REPORT"
