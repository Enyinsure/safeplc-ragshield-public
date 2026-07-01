# S7 Agent v2 交付包解包自检报告

## 测试时间
Thu May 14 01:25:55 PM CST 2026

## 1. 文件存在性检查

-rw-rw-r-- 1 user user 103 May 14 13:23 S7_MULTIMODAL_RAG_V1_AGENT_V2.sha256
-rw-rw-r-- 1 user user 20M May 14 13:23 S7_MULTIMODAL_RAG_V1_AGENT_V2.tar.gz

## 2. sha256 校验

```text
S7_MULTIMODAL_RAG_V1_AGENT_V2.tar.gz: OK
```

## 3. 解包目录

`~/release_selfcheck_agent_v2`

## 4. 核心文件检查

```text
-rw-rw-r-- 1 user user  24K May 14 13:19 release_selfcheck_agent_v2/agent_v2_acceptance_report.md
-rw-rw-r-- 1 user user 4.1K May 14 13:20 release_selfcheck_agent_v2/PROJECT_FINAL_STATUS_AGENT_V2.txt
-rwxrwxr-x 1 user user 3.1K May 14 13:16 release_selfcheck_agent_v2/run_agent_v2_acceptance.sh
-rwxrwxr-x 1 user user  289 May 14 13:07 release_selfcheck_agent_v2/run_streamlit_s7_rag_agent_v2.sh
-rwxrwxr-x 1 user user 7.3K May 14 13:07 release_selfcheck_agent_v2/s7_multimodal_v1/agent_clarifier_v2.py
-rwxrwxr-x 1 user user 8.0K May 14 12:16 release_selfcheck_agent_v2/s7_multimodal_v1/agent_planner_v1.py
-rwxrwxr-x 1 user user 3.0K May 14 13:07 release_selfcheck_agent_v2/s7_multimodal_v1/app_streamlit_agent_v2.py
-rwxrwxr-x 1 user user 2.6K May 14 12:16 release_selfcheck_agent_v2/s7_multimodal_v1/ask_s7_agent_v1.py
-rwxrwxr-x 1 user user 2.5K May 14 13:07 release_selfcheck_agent_v2/s7_multimodal_v1/ask_s7_agent_v2.py
-rw-rw-r-- 1 user user  16K May 13 20:26 release_selfcheck_agent_v2/s7_multimodal_v1/ask_s7_multimodal_final.py
-rwxrwxr-x 1 user user 4.8K May 14 11:57 release_selfcheck_agent_v2/s7_multimodal_v1/ask_s7_multimodal_final_safety.py
-rw-rw-r-- 1 user user 282K May 13 11:38 release_selfcheck_agent_v2/s7_multimodal_v1/images/visual_candidate_pages/page_0641.jpg
-rw-rw-r-- 1 user user 187K May 13 11:38 release_selfcheck_agent_v2/s7_multimodal_v1/images/visual_candidate_pages/page_2478.jpg
-rw-r--r-- 1 user user 764K May 14 13:22 release_selfcheck_agent_v2/s7_multimodal_v1/index/chroma_figures_v1/chroma.sqlite3
-rwxrwxr-x 1 user user 5.2K May 14 11:56 release_selfcheck_agent_v2/s7_multimodal_v1/safety_guard_v1.py
```

## 5. Agent v2 澄清层快速测试

```text
某个模块的电源电压允许范围是多少
  context: 无
  enhanced: 某个模块的电源电压允许范围是多少
  clarify: True
  execute: False
  safety: MEDIUM_RISK
某个模块的电源电压允许范围是多少
  context: PS 60W 24/48/60VDC HF
  enhanced: PS 60W 24/48/60VDC HF 电源电压允许范围是多少
  clarify: False
  execute: True
  safety: MEDIUM_RISK
PROFINET 环网如何连接 HMI 设备
  context: 无
  enhanced: PROFINET 环网如何连接 HMI 设备
  clarify: False
  execute: True
  safety: MEDIUM_RISK
能不能带电接 24V 电源端子
  context: 无
  enhanced: 能不能带电接 24V 电源端子
  clarify: False
  execute: True
  safety: HIGH_RISK
EMC 要求是什么
  context: 无
  enhanced: EMC 要求是什么
  clarify: False
  execute: True
  safety: SAFE_INFO
```

## 6. Agent v2 命令行入口快速测试

```text
【Agent v2 澄清判断】
【原始问题】某个模块的电源电压允许范围是多少
【补充上下文】无
【增强后问题】某个模块的电源电压允许范围是多少
【Agent v1 问题类型】spec_or_table_query
【安全等级】MEDIUM_RISK
【建议检索策略】table_first
【缺失信息】具体 CPU / 模块型号或订货号；电源类型和对应模块，例如系统电源、负载电源或具体 PS/CPU 型号；被询问对象的完整名称，例如 CPU 1517-3 PN 或 PS 60W 24/48/60VDC HF
【是否需要澄清】是
【是否继续执行】否
【判断理由】当前问题缺少关键型号、订货号或对象信息；为避免误命中其它模块，Agent v2 将先追问而不是直接检索。

【建议追问】
- 请补充具体 CPU / 模块型号或订货号，例如 CPU 1517-3 PN、PS 60W 24/48/60VDC HF 或 6ES7...。
- 请说明要查询的是系统电源、负载电源、CPU 本体电源，还是某个 PS/PM 电源模块。
- 请给出被询问对象的完整名称，避免把其它模块的参数误当作答案。

【可参考问法】
- PS 60W 24/48/60VDC HF 电源电压允许范围是多少
- CPU 1517-3 PN 的电源电压允许范围是多少
- 6ES7505-0RB00-0AB0 的电源电压允许范围是多少

【Agent v2 执行结果】
当前问题需要先补充关键信息。Agent v2 已停止自动检索，避免误命中其它模块并输出误导性参数。

你可以使用如下方式继续：
python ask_s7_agent_v2.py "某个模块的电源电压允许范围是多少" --context "PS 60W 24/48/60VDC HF"

【Agent v2 澄清判断】
【原始问题】某个模块的电源电压允许范围是多少
【补充上下文】PS 60W 24/48/60VDC HF
【增强后问题】PS 60W 24/48/60VDC HF 电源电压允许范围是多少
【Agent v1 问题类型】spec_or_table_query
【安全等级】MEDIUM_RISK
【建议检索策略】table_first
【缺失信息】具体 CPU / 模块型号或订货号；电源类型和对应模块，例如系统电源、负载电源或具体 PS/CPU 型号；被询问对象的完整名称，例如 CPU 1517-3 PN 或 PS 60W 24/48/60VDC HF
【是否需要澄清】否
【是否继续执行】是
【判断理由】用户已补充上下文，Agent v2 将使用增强后的问题继续执行。

【建议追问】
- 无

【可参考问法】
- 无

【Agent v2 调用 Agent v1】
执行问题：PS 60W 24/48/60VDC HF 电源电压允许范围是多少

【Agent v2 最终回答】
【Agent 主动推理环 v1】
【问题类型】spec_or_table_query
【安全等级】MEDIUM_RISK
【建议检索策略】table_first
【缺失信息提示】无

【证据目标】
- 表格证据：技术规范、技术数据、允许范围、额定值

【推理说明】
- Safety Guard v1 判定风险等级为 MEDIUM_RISK。
- Agent v1 将问题识别为 spec_or_table_query。
- 建议检索策略为 table_first。
- 问题具备直接检索和回答的基本条件。

【Agent 执行结果】
【工业安全护栏】已启用
【安全等级】MEDIUM_RISK
【命中关键词】dc、电源、电源电压
【是否需要人工复核】是
【安全提示】该问题涉及工业设备接线、电源、端子、接口或通信连接。以下回答仅基于手册内容说明，不替代现场电气设计、调试规程或安全审核。实际操作前应断电，并由具备资质的人员核对订货号、端子定义、额定电压、现场图纸和厂家手册。

【原 RAG 回答】
问题：PS 60W 24/48/60VDC HF 电源电压允许范围是多少
路由：table
================================================================================
答案
--------------------------------------------------------------------------------
PS 60W 24/48/60VDC HF 的电源电压参数为：
- 额定值：24 V / 48 V / 60 V
- 允许范围下限：静态 19.2 V，动态 18.5 V
- 允许范围上限：静态 72 V，动态 75.5 V

依据
--------------------------------------------------------------------------------
页码：6313
章节：设备特定信息 > 系统功率模块 > 电源模块 PS 60W 24/48/60VDC HF (6ES7505-0RB00-0AB0) > 6 技术规范

关键证据
--------------------------------------------------------------------------------
STEP 7 TIA 端口，可组态 / 已集成，自版本
14 版 SP1
电源电压
额定值 (DC)
24 V / 48 V / 60 V
允许范围，下限 (DC)
静态 19.2 V，动态 18.5 V
允许范围，上限 (DC)
静态 72 V，动态 75.5 V
反极性保护
是
短路保护
是
电源和电压断路跨接
•
停电/断电跨接时间
20 ms
输入电流
DC 24 V 时的额定值
3 A

图文补充
--------------------------------------------------------------------------------
[1] page=643 figure_id=page_0643_visual type=text_with_small_figure score=2.2071
    系统电源
[2] page=2227 figure_id=page_2227_visual type=wiring_diagram score=2.1653
    介绍了 CPU 1515T-2 PN 的接线信息和方框图。
[3] page=4866 figure_id=page_4866_visual type=wiring_diagram score=2.1648
    电源器件的针脚分配

【Agent v2 澄清判断】
【原始问题】能不能带电接 24V 电源端子
【补充上下文】无
【增强后问题】能不能带电接 24V 电源端子
【Agent v1 问题类型】high_risk_operation
【安全等级】HIGH_RISK
【建议检索策略】safety_block
【缺失信息】无
【是否需要澄清】否
【是否继续执行】是
【判断理由】高风险问题优先交由 Safety Guard v1 输出完整拒答，不要求用户补充操作细节。

【建议追问】
- 无

【可参考问法】
- 无

【Agent v2 调用 Agent v1】
执行问题：能不能带电接 24V 电源端子

【Agent v2 最终回答】
【Agent 主动推理环 v1】
【问题类型】high_risk_operation
【安全等级】HIGH_RISK
【建议检索策略】safety_block
【缺失信息提示】无

【证据目标】
- 安全护栏：拒绝危险操作步骤，仅允许安全边界说明

【推理说明】
- Safety Guard v1 判定风险等级为 HIGH_RISK。
- Agent v1 将问题识别为 high_risk_operation。
- 建议检索策略为 safety_block。
- 问题具备直接检索和回答的基本条件。

【Agent 执行结果】
【工业安全护栏】已启用
【安全等级】HIGH_RISK
【命中关键词】带电、接
【是否需要人工复核】是
【安全提示】该问题涉及高风险现场操作。我不能提供可能导致人身伤害、设备损坏、绕过保护机制或违反现场安全规程的具体操作步骤。可以提供手册中的端子定义、额定参数、风险点和安全检查清单。实际操作必须由具备资质的人员在断电、挂牌上锁和现场审核后执行。

【回答】
该问题涉及高风险现场操作，不能提供具体执行步骤。为了安全起见，建议改为查询以下信息：端子定义、额定电压/电流、允许范围、通信接口说明、厂家手册中的安全注意事项，或现场操作前检查清单。

【可安全提供的信息类型】
- 手册中的端子名称和功能说明
- 额定电压、电流、允许范围等技术参数
- PROFINET / PROFIBUS / RJ45 等接口的说明性信息
- 需要人工复核的风险点清单

【结论】
请勿根据聊天回答直接进行带电接线、短接、屏蔽保护、强制输出或绕过安全回路等操作。
```

## 7. 包清单摘要

```text
s7_multimodal_v1/
s7_multimodal_v1/images/
s7_multimodal_v1/images/sample_20pages/
s7_multimodal_v1/images/sample_20pages/fig20p_0001_66ae855338bf4e09de7992b607d6dd34f9d4a6ebfb597fe12798c8f8160ce8f6.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0002_8dea16769f477eaa8e27e992d68a9dbc0ae1aa1e824c0e9fcfbaa13df291e69b.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0003_326db806db4283925670916c7836c727904d17a78f42fae9cfb1541416ad6fbd.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0004_0ac266f4e5b1280a723748a2198aac36ce1aaaa42dc8b08413e6396141bf0096.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0006_86b32110e2e3f84ab4830c41bcb4edd0e9504f23a69fc65c095af07b785bb74d.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0007_24c5b37eef7240663f9307536535b249f0bb2bc5fd756a9a6b3c45dac8a8717c.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0008_25309cadbb6ddb0a41e573487977aa419b2e8e17b3640d229f67ca26b48fda50.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0010_878b98d099c1700669c5d70cccb05345f1aa11a56ed981b2d08084adf70deeea.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0014_9ee4bb85ac551ce08def8fe216c53db525cb1f9e6643c6cb56dbae1bbca5da97.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0016_345975085ac1c340dedd0959bc0cf373b2b961113093f6dbd2937fda90376200.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0005_5504d17f1e3a00cc58a3a19db6763393149fca5627cd7ee0d494f4b6b4f065a8.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0009_6de213546bc298f2f63023d9f211691d5329a7e1ce3508730402bb8af37fcb57.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0011_95720171e3755c758fb74a4c2d4d1bd7c9abed08171c359107feda9c07744edc.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0012_811d1744e961ddce5697ebc75cb8119fff49d245c92dc9c82b1b73f302cb6fdd.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0013_4ccab63faafe67376ca281bd746c4bfe2e65b73df295627857801d55ac738d3c.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0015_3a6fec1de098b4945d402af57693adc27b0e1cf1e3b0eb45ea3476cbce115171.jpg
s7_multimodal_v1/images/sample_20pages/fig20p_0017_760ce4b1f7b1d7f4e3370136a508bca4a951df121835d7dadd21e93221c81c17.jpg
s7_multimodal_v1/images/contact_sheets/
s7_multimodal_v1/images/contact_sheets/visual_contact_sheet_03.jpg
s7_multimodal_v1/images/contact_sheets/visual_contact_sheet_04.jpg
s7_multimodal_v1/images/contact_sheets/visual_contact_sheet_06.jpg
s7_multimodal_v1/images/contact_sheets/visual_contact_sheet_07.jpg
s7_multimodal_v1/images/contact_sheets/visual_contact_sheet_01.jpg
s7_multimodal_v1/images/contact_sheets/visual_contact_sheet_02.jpg
s7_multimodal_v1/images/contact_sheets/visual_contact_sheet_05.jpg
s7_multimodal_v1/images/visual_candidate_pages/
s7_multimodal_v1/images/visual_candidate_pages/page_1760.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0160.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8449.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0208.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8728.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0148.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0183.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0209.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_6250.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_6283.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_6306.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_6327.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_4949.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0641.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2773.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2918.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0157.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_1045.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8700.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8829.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0644.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0673.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_1682.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2633.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2723.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0098.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0425.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0744.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2384.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_3110.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8448.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0096.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0206.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8506.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0643.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0646.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0674.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0886.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0180.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2041.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0676.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0207.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0162.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0661.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0159.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0202.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0150.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0354.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0680.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2996.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8172.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8726.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0647.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0889.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_3907.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_4866.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8528.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0163.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2323.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_5055.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0662.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0677.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_5411.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2860.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_3877.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_5121.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8530.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_8587.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0424.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_9635.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0211.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_1044.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0185.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2126.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2227.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2478.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2517.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_1959.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_0156.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2616.jpg
s7_multimodal_v1/images/visual_candidate_pages/page_2862.jpg
s7_multimodal_v1/chunks/
s7_multimodal_v1/chunks/s7_figure_chunks_v1.jsonl
s7_multimodal_v1/logs/
s7_multimodal_v1/logs/vlm_raw_outputs_repair/
s7_multimodal_v1/logs/vlm_raw_outputs_repair/page_0208_visual.txt
s7_multimodal_v1/logs/vlm_raw_outputs_repair/page_0641_visual.txt
s7_multimodal_v1/logs/vlm_raw_outputs_repair/page_0098_visual.txt
s7_multimodal_v1/logs/vlm_raw_outputs_repair/page_0180_visual.txt
s7_multimodal_v1/logs/vlm_raw_outputs_repair/page_0889_visual.txt
s7_multimodal_v1/logs/vlm_raw_outputs_repair/page_2227_visual.txt
```

## 结论

通过。

Agent v2 交付包解包自检通过：
- 交付包和 sha256 文件存在。
- sha256 校验通过。
- 解包目录创建成功。
- Agent v2 澄清层、命令行入口、Streamlit 前端完整。
- Agent v1、Safety Guard v1、原多模态 RAG 入口完整。
- 图文 ChromaDB 核心文件存在。
- 关键证据图片 page_2478.jpg 和 page_0641.jpg 存在。
- Agent v2 澄清层快速测试通过。
- Agent v2 命令行入口快速测试通过。

封版结论：
S7 多模态 RAG v1 Agent v2 多轮澄清 / 自动追问 / 交互式前端交付包可交付。
