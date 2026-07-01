#!/usr/bin/env bash
set -u

QA_FILE="${HOME}/s7_multimodal_stress_questions_v1.txt"
APP="${HOME}/s7_multimodal_v1/ask_s7_multimodal_final.py"
OUT="${HOME}/multimodal_stress_test_v1.md"

echo "# S7 多模态 RAG v1 压力测试报告" > "$OUT"
echo >> "$OUT"
echo "测试入口：$APP" >> "$OUT"
echo "问题集：$QA_FILE" >> "$OUT"
echo >> "$OUT"

i=0
pass=0
fail=0

while IFS= read -r q; do
  [ -z "$q" ] && continue
  i=$((i+1))

  echo "===== [$i] $q ====="
  echo "## [$i] $q" >> "$OUT"
  echo '```text' >> "$OUT"

  if timeout 240 python "$APP" "$q" >> "$OUT" 2>&1; then
    echo "PASS: $q"
    pass=$((pass+1))
    echo '```' >> "$OUT"
    echo >> "$OUT"
    echo "**状态：PASS**" >> "$OUT"
  else
    echo "FAIL: $q"
    fail=$((fail+1))
    echo '```' >> "$OUT"
    echo >> "$OUT"
    echo "**状态：FAIL**" >> "$OUT"
  fi

  echo >> "$OUT"
done < "$QA_FILE"

{
  echo
  echo "## 汇总"
  echo
  echo "- 总数：$i"
  echo "- 通过：$pass"
  echo "- 失败：$fail"
} >> "$OUT"

echo "DONE"
echo "总数：$i，通过：$pass，失败：$fail"
echo "报告：$OUT"
