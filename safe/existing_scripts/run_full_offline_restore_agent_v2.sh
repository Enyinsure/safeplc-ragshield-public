#!/usr/bin/env bash
set -e

cd ~

PKG=S7_MULTIMODAL_RAG_V1_AGENT_V2.tar.gz
SHA=S7_MULTIMODAL_RAG_V1_AGENT_V2.sha256
OUTDIR=full_restore_agent_v2
REPORT=full_offline_restore_test_agent_v2.md

{
  echo "# S7 多模态 RAG Agent v2 最终全量离线恢复测试报告"
  echo
  echo "## 测试时间"
  date
  echo
  echo "## 测试目标"
  echo
  echo "在全新目录中模拟交付部署，验证 Agent v2 最终包可校验、可解包、可运行命令行、可执行安全拒答、可执行多轮澄清，并具备前端启动条件。"
  echo
} > "$REPORT"

echo "[1/9] 检查最终包"
{
  echo "## 1. 最终包文件检查"
  echo
  echo '```text'
  ls -lh "$PKG" "$SHA"
  echo '```'
  echo
} >> "$REPORT"

echo "[2/9] sha256 校验"
{
  echo "## 2. sha256 校验"
  echo
  echo '```text'
  sha256sum -c "$SHA"
  echo '```'
  echo
} >> "$REPORT"

echo "[3/9] 清理并解包到全新目录"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

tar -xzf "$PKG" -C "$OUTDIR"

{
  echo "## 3. 解包目录"
  echo
  echo "\`~/$OUTDIR\`"
  echo
} >> "$REPORT"

echo "[4/9] 检查核心文件"
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
    "$OUTDIR/s7_multimodal_v1/images/visual_candidate_pages/page_0641.jpg" \
    "$OUTDIR/s7_multimodal_v1/images/visual_candidate_pages/page_2478.jpg" \
    "$OUTDIR/run_streamlit_s7_rag_agent_v2.sh" \
    "$OUTDIR/PROJECT_FINAL_STATUS_AGENT_V2.txt"
  echo '```'
  echo
} >> "$REPORT"

echo "[5/9] Python 模块导入测试"
{
  echo "## 5. Python 模块导入测试"
  echo
  echo '```text'
  cd "${HOME}/${OUTDIR}/s7_multimodal_v1"
  python - <<'PY'
import importlib

mods = [
    "safety_guard_v1",
    "agent_planner_v1",
    "agent_clarifier_v2",
]

for m in mods:
    importlib.import_module(m)
    print(f"{m}: OK")

try:
    import chromadb
    print("chromadb: OK")
except Exception as e:
    print("chromadb: FAIL", e)

try:
    import sentence_transformers
    print("sentence_transformers: OK")
except Exception as e:
    print("sentence_transformers: FAIL", e)

try:
    import streamlit
    print("streamlit: OK")
except Exception as e:
    print("streamlit: FAIL", e)
PY
  echo '```'
  echo
} >> "${HOME}/${REPORT}"

cd ~

echo "[6/9] Agent v2 澄清机制测试"
{
  echo "## 6. Agent v2 澄清机制测试"
  echo
  echo '```text'
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v2.py" "某个模块的电源电压允许范围是多少"
  echo '```'
  echo
} >> "$REPORT"

echo "[7/9] Agent v2 补充上下文后执行测试"
{
  echo "## 7. Agent v2 补充上下文后执行测试"
  echo
  echo '```text'
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v2.py" \
    "某个模块的电源电压允许范围是多少" \
    --context "PS 60W 24/48/60VDC HF"
  echo '```'
  echo
} >> "$REPORT"

echo "[8/9] Agent v2 图文问题与高风险拒答测试"
{
  echo "## 8. 图文问题与高风险拒答测试"
  echo
  echo "### 8.1 PROFINET / HMI 图文问题"
  echo
  echo '```text'
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v2.py" \
    "PROFINET 环网如何连接 HMI 设备"
  echo '```'
  echo
  echo "### 8.2 高风险问题"
  echo
  echo '```text'
  python "$OUTDIR/s7_multimodal_v1/ask_s7_agent_v2.py" \
    "能不能带电接 24V 电源端子"
  echo '```'
  echo
} >> "$REPORT"

echo "[9/9] 前端可启动性静态检查"
{
  echo "## 9. Agent v2 Streamlit 前端可启动性检查"
  echo
  echo '```text'
  python -m py_compile "$OUTDIR/s7_multimodal_v1/app_streamlit_agent_v2.py"
  echo "app_streamlit_agent_v2.py: py_compile OK"
  ls -lh "$OUTDIR/run_streamlit_s7_rag_agent_v2.sh"
  echo
  echo "前端启动命令："
  echo "bash ~/$OUTDIR/run_streamlit_s7_rag_agent_v2.sh"
  echo '```'
  echo
  echo "## 结论"
  echo
  echo "待人工复核。"
} >> "$REPORT"

echo "[OK] 最终全量离线恢复测试完成：~/$REPORT"
