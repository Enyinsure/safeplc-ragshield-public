# S7 Multimodal RAG v1

## 状态

S7-1500 / ET 200MP 中文手册多模态 RAG v1 检索层已完成。

## 已完成内容

1. 人工筛选视觉高价值页。
2. PDF 整页渲染为图片。
3. 使用 Qwen2.5-VL-3B-Instruct 本地 VLM 生成图像语义卡片。
4. 生成 figure_cards_v1.jsonl，共 37 条。
5. 修复/兜底后 parse failed = 0。
6. fallback 兜底卡片 4 条，均标记 needs_human_review。
7. 生成 s7_figure_chunks_v1.jsonl，共 37 条。
8. 建立 ChromaDB 图文索引 s7_figures_v1。
9. 完成图文 rerank 查询脚本。
10. 完成多模态优先路由入口 ask_s7_multimodal_priority.py。

## 关键路径

- 图像语义卡片：
  ~/s7_multimodal_v1/figure_cards/figure_cards_v1.jsonl

- 图文 chunks：
  ~/s7_multimodal_v1/chunks/s7_figure_chunks_v1.jsonl

- 图文 ChromaDB：
  ~/s7_multimodal_v1/index/chroma_figures_v1

- 图文查询脚本：
  ~/s7_multimodal_v1/query_s7_figures_v1_rerank.py

- 多模态优先路由入口：
  ~/s7_multimodal_v1/ask_s7_multimodal_priority.py

## 环境说明

- VLM 生成阶段使用 vlm_qwen 环境。
- ChromaDB / RAG 检索阶段使用 s7rag 环境。
- Qwen2.5-VL-3B-Instruct 只用于图像语义卡片生成。
- Chroma embedding 沿用原 RAG 的 BAAI/bge-small-zh-v1.5。

## 验证样例

python ~/s7_multimodal_v1/ask_s7_multimodal_priority.py "CPU 1517-3 PN 的 PROFINET 接口 X1 X2"

python ~/s7_multimodal_v1/ask_s7_multimodal_priority.py "PROFINET 环网如何连接 HMI 设备"

python ~/s7_multimodal_v1/ask_s7_multimodal_priority.py "24 V DC 电源电压端子怎么接线"

python ~/s7_multimodal_v1/ask_s7_multimodal_priority.py "PS 60W 24/48/60DC HF 电源电压允许范围是多少"
