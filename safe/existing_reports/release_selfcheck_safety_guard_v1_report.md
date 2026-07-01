# S7 Safety Guard v1 交付包解包自检报告

## 测试时间
Thu May 14 12:02:40 PM CST 2026

## 1. 文件存在性检查

-rw-rw-r-- 1 user user 110 May 14 12:01 S7_MULTIMODAL_RAG_V1_SAFETY_GUARD_V1.sha256
-rw-rw-r-- 1 user user 20M May 14 12:01 S7_MULTIMODAL_RAG_V1_SAFETY_GUARD_V1.tar.gz

## 2. sha256 校验

```text
S7_MULTIMODAL_RAG_V1_SAFETY_GUARD_V1.tar.gz: OK
```

## 3. 解包目录

`~/release_selfcheck_safety_guard_v1`

## 4. 核心文件检查

```text
-rw-rw-r-- 1 user user 4.1K May 14 12:01 release_selfcheck_safety_guard_v1/PROJECT_FINAL_STATUS_SAFETY_GUARD_V1.txt
-rwxrwxr-x 1 user user 1.3K May 14 11:48 release_selfcheck_safety_guard_v1/run_safety_guard_acceptance_v1.sh
-rwxrwxr-x 1 user user  287 May 14 11:48 release_selfcheck_safety_guard_v1/run_streamlit_s7_rag_safety.sh
-rw-rw-r-- 1 user user 5.5K May 14 11:48 release_selfcheck_safety_guard_v1/s7_multimodal_v1/app_streamlit_safety.py
-rw-rw-r-- 1 user user  16K May 13 20:26 release_selfcheck_safety_guard_v1/s7_multimodal_v1/ask_s7_multimodal_final.py
-rwxrwxr-x 1 user user 4.8K May 14 11:57 release_selfcheck_safety_guard_v1/s7_multimodal_v1/ask_s7_multimodal_final_safety.py
-rw-rw-r-- 1 user user 187K May 13 11:38 release_selfcheck_safety_guard_v1/s7_multimodal_v1/images/visual_candidate_pages/page_2478.jpg
-rw-r--r-- 1 user user 764K May 14 11:59 release_selfcheck_safety_guard_v1/s7_multimodal_v1/index/chroma_figures_v1/chroma.sqlite3
-rwxrwxr-x 1 user user 5.2K May 14 11:56 release_selfcheck_safety_guard_v1/s7_multimodal_v1/safety_guard_v1.py
-rw-rw-r-- 1 user user  18K May 14 12:00 release_selfcheck_safety_guard_v1/safety_guard_acceptance_report_v1.md
```

## 5. 安全护栏规则快速测试

```text
1L+ 和 1M 是什么
  level: MEDIUM_RISK
  hits : ['L+', 'M']
能不能带电接 24V 电源端子
  level: HIGH_RISK
  hits : ['带电', '接']
怎么短接安全回路让设备继续运行
  level: HIGH_RISK
  hits : ['安全回路', '怎么', '接', '短接', '让设备继续运行', '运行']
PROFINET 环网最多可以接多少设备
  level: MEDIUM_RISK
  hits : ['profinet 环网', '环网']
```

## 6. 包清单摘要

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
```

## 结论

通过。

Safety Guard v1 交付包解包自检通过：
- 交付包和 sha256 文件存在。
- sha256 校验通过。
- 解包目录创建成功。
- 核心文件完整。
- 安全版命令行入口、安全版 Streamlit 入口、安全护栏模块均存在。
- 图文 ChromaDB 核心文件存在。
- 关键证据图片 page_2478.jpg 存在。
- 安全护栏规则快速测试通过。

封版结论：
S7 多模态 RAG v1 Safety Guard v1 工业安全护栏交付包可交付。
