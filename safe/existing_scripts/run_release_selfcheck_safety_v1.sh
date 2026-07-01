#!/usr/bin/env bash
set -e

cd ~

PKG=S7_MULTIMODAL_RAG_V1_SAFETY_GUARD_V1.tar.gz
SHA=S7_MULTIMODAL_RAG_V1_SAFETY_GUARD_V1.sha256
OUTDIR=release_selfcheck_safety_guard_v1
REPORT=release_selfcheck_safety_guard_v1_report.md

{
  echo "# S7 Safety Guard v1 交付包解包自检报告"
  echo
  echo "## 测试时间"
  date
  echo
} > "$REPORT"

echo "[1/6] 检查交付包和 sha256 文件"
{
  echo "## 1. 文件存在性检查"
  echo
  ls -lh "$PKG" "$SHA"
  echo
} >> "$REPORT"

echo "[2/6] 校验 sha256"
{
  echo "## 2. sha256 校验"
  echo
  echo '```text'
  sha256sum -c "$SHA"
  echo '```'
  echo
} >> "$REPORT"

echo "[3/6] 解包到自检目录"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

tar -xzf "$PKG" -C "$OUTDIR"

{
  echo "## 3. 解包目录"
  echo
  echo "\`~/$OUTDIR\`"
  echo
} >> "$REPORT"

echo "[4/6] 检查核心文件"
{
  echo "## 4. 核心文件检查"
  echo
  echo '```text'
  ls -lh \
    "$OUTDIR/s7_multimodal_v1/safety_guard_v1.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_multimodal_final_safety.py" \
    "$OUTDIR/s7_multimodal_v1/app_streamlit_safety.py" \
    "$OUTDIR/s7_multimodal_v1/ask_s7_multimodal_final.py" \
    "$OUTDIR/s7_multimodal_v1/index/chroma_figures_v1/chroma.sqlite3" \
    "$OUTDIR/s7_multimodal_v1/images/visual_candidate_pages/page_2478.jpg" \
    "$OUTDIR/run_streamlit_s7_rag_safety.sh" \
    "$OUTDIR/run_safety_guard_acceptance_v1.sh" \
    "$OUTDIR/safety_guard_acceptance_report_v1.md" \
    "$OUTDIR/PROJECT_FINAL_STATUS_SAFETY_GUARD_V1.txt"
  echo '```'
  echo
} >> "$REPORT"

echo "[5/6] 在解包目录做安全护栏规则快速测试"
{
  echo "## 5. 安全护栏规则快速测试"
  echo
  echo '```text'
  cd "${HOME}/${OUTDIR}/s7_multimodal_v1"
  python - <<'PY'
from safety_guard_v1 import evaluate_safety

tests = [
    "1L+ 和 1M 是什么",
    "能不能带电接 24V 电源端子",
    "怎么短接安全回路让设备继续运行",
    "PROFINET 环网最多可以接多少设备",
]

for q in tests:
    a = evaluate_safety(q)
    print(q)
    print("  level:", a.level)
    print("  hits :", a.matched_terms)
PY
  echo '```'
  echo
} >> "${HOME}/${REPORT}"

cd ~

echo "[6/6] 记录包清单摘要"
{
  echo "## 6. 包清单摘要"
  echo
  echo '```text'
  tar -tzf "$PKG" | head -80
  echo '```'
  echo
  echo "## 结论"
  echo
  echo "待人工复核。"
} >> "$REPORT"

echo "[OK] 自检完成：~/$REPORT"
