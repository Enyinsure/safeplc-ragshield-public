# S7-1500 / ET 200MP 中文手册 RAG 最终说明

## 已完成模块

1. 文本 RAG v3
- 清洗 Siemens 页眉页脚、版权、A5E 噪声
- 生成 s7_chunks_v2.jsonl
- 构建 ChromaDB
- 支持单条问答 ask_s7_stable.py
- 支持批量问答 ask_s7_batch.py

2. 跨页表格合并 v4
- 输入 MinerU middle/content table
- 识别跨页表格
- 过滤重叠跨页组
- 输出 stitched_tables.json / stitched.md

3. 表格优先问答
- 生成 s7_table_chunks_v4.jsonl
- 支持表格类问题优先查询
- 入口 ask_s7_tables_priority_stable.py

4. Markdown 表格恢复
- 将 HTML table 恢复成 Markdown 表格
- 输出 stitched_tables_restored.md
- 输出 stitched_tables_restored.json
- 输出 table_markdown_report.txt

## 常用命令

文本问答：

```bash
conda activate s7rag
python ~/ask_s7_stable.py "CPU 1511 工作存储器是多少？"
