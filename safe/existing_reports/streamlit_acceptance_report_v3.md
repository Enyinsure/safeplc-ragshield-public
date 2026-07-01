# S7 多模态 RAG Streamlit 前端 v3 验收报告

## 验收结论

通过。

## 前端入口

~/s7_multimodal_v1/app_streamlit.py

## 后端入口

~/s7_multimodal_v1/ask_s7_multimodal_final.py

## 运行环境

conda activate s7rag_ui

## 启动命令

streamlit run ~/s7_multimodal_v1/app_streamlit.py \
  --server.address 0.0.0.0 \
  --server.port 8501

## 本版新增功能

1. 分区显示答案、依据、关键证据、图文补充。
2. 支持展开查看原始完整输出。
3. 支持 figure 路由时自动解析页码。
4. 支持显示对应图文证据页面图片。
5. 支持展示证据图片路径。

## 已验证样例

### 1. CPU 1517-3 PN 的 PROFINET 接口 X1 X2

- 路由：figure
- 页码：2478
- 图文证据图片：page_2478.jpg
- 结论：通过

### 2. PROFINET 环网如何连接 HMI 设备

- 路由：figure
- 页码：641
- 图文证据图片：page_0641.jpg
- 结论：通过

### 3. PS 60W 24/48/60DC HF 电源电压允许范围是多少

- 路由：table
- 结论：通过
- 说明：表格问题主证据以文本/表格为主，前端正常提示 table 路由。

## 结论

Streamlit 前端 v3 图文证据图片展示功能通过验收，可作为展示版前端。
