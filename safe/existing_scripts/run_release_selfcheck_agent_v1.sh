#!/usr/bin/env bash
set -e

cd ~

PKG=S7_MULTIMODAL_RAG_V1_AGENT_V1.tar.gz
SHA=S7_MULTIMODAL_RAG_V1_AGENT_V1.sha256
OUTDIR=release_selfcheck_agent_v1
REPORT=release_selfcheck_agent_v1_report.md

{
  echo "# S7 Agent v1 交付包解包自检报告"
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
    "$OUTDIR/s7_multimodal_v1/agent_planner_v1.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v1.py" \
    "$OUTDIR/s7_multimodal_v1/app_streamlit_agent_v1.py" \
    "$OUTDIR/s7_multimodal_v1/safety_guard_v1.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_multimodal_final_safety.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_multimodal_final.py" \
    "$OUTDIR/s7_multimodal_v1/index/chroma_figures_v1/chroma.sqlite3" \
    "$OUTDIR/s7_multimodal_v1/images/visual_candidate_pages/page_2478.jpg" \
    "$OUTDIR/s7_multimodal_v1/images/visual_candidate_pages/page_0641.jpg" \
    "$OUTDIR/run_streamlit_s7_rag_agent_v1.sh" \
    "$OUTDIR/run_agent_acceptance_v1.sh" \
    "$OUTDIR/agent_acceptance_report_v1.md" \
    "$OUTDIR/PROJECT_FINAL_STATUS_AGENT_V1.txt"
  echo '```'
  echo
} >> "$REPORT"

echo "[5/7] 测试 Agent planner 导入和规划"
{
  echo "## 5. Agent planner 快速测试"
  echo
  echo '```text'
  cd "${HOME}/${OUTDIR}/s7_multimodal_v1"
  python - <<'PY'
from agent_planner_v1 import make_agent_plan

tests = [
    "CPU 1517-3 PN 的 PROFINET 接口 X1 X2",
    "某个模块的电源电压允许范围是多少",
    "能不能带电接 24V 电源端子",
    "PROFINET 环网如何连接 HMI 设备",
    "EMC 要求是什么",
]

for q in tests:
    p = make_agent_plan(q)
    print(q)
    print("  intent:", p.agent_intent)
    print("  safety:", p.safety_level)
    print("  route :", p.preferred_route)
    print("  missing:", "；".join(p.missing_info) if p.missing_info else "无")
    print("  call_rag:", p.should_call_rag)
PY
  echo '```'
  echo
} >> "${HOME}/${REPORT}"

cd ~

echo "[6/7] 测试 Agent 命令行入口"
{
  echo "## 6. Agent 命令行入口快速测试"
  echo
  echo '```text'
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v1.py" "PROFINET 环网最多可以接多少设备"
  echo
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v1.py" "某个模块的电源电压允许范围是多少"
  echo
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v1.py" "能不能带电接 24V 电源端子"
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

echo "[OK] Agent v1 自检完成：~/$REPORT"
