# S7 多模态 RAG Streamlit 前端 v2 验收报告

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

## 已验证样例

### 1. CPU 1517-3 PN 的 PROFINET 接口 X1 X2

- 路由：figure
- 结论：通过
- 说明：正确显示答案、依据、补充图文证据和原始完整输出。

### 2. PS 60W 24/48/60DC HF 电源电压允许范围是多少

- 路由：table
- 结论：通过
- 说明：正确显示答案、依据、关键证据、图文补充和原始完整输出。

### 3. PROFINET 环网如何连接 HMI 设备

- 路由：figure
- 结论：通过
- 说明：正确显示 HMI、PROFINET 环网、X2/X3 接口和设备数量限制相关信息。

## 前端功能

1. 左侧样例问题选择。
2. 用户自定义问题输入。
3. 一键调用最终 RAG 入口。
4. 显示路由类型。
5. 显示检索耗时。
6. 分区展示答案、依据、关键证据、图文补充。
7. 支持展开查看原始完整输出。

## 结论

Streamlit 前端 v2 联调通过，可纳入展示版交付包。
