# Visual Evidence Card Schema

## 1. Visual Evidence DB Positioning

视觉证据库并非简单图片索引，而是面向工业运维任务构建的多模态可信证据基座。系统将 PLC 手册中的接线图、端子图、报警诊断页、模块面板图、网络拓扑图和参数表统一封装为结构化证据卡，并保留页码、章节、图像路径、文本摘要、证据哈希和工业语义类型，为后续证据污染检测、风险证据保留、国密审计和防篡改验证提供可信基础。

## 2. Evidence Card Fields

| Field | Definition |
| --- | --- |
| evidence_id | Stable evidence identifier, for example `pdf_page_01965`. |
| source_pdf | Source manual or PDF identifier. |
| source_type | Extraction source such as `pdf_page_render`, `ocr`, `table`, or `chroma_visual_v2`. |
| modality | Evidence modality: image, OCR text, table, diagram, or mixed. |
| page | Manual page number. |
| section | Manual section or heading. |
| visual_type | Industrial semantic visual category. |
| risk_tags | Safety/risk labels detected during extraction. |
| matched_keywords | Keywords that explain retrieval or risk matching. |
| text | OCR/table/summary text used by retrieval and M-EPI. |
| source_image_path | Local path to rendered page or cropped visual asset. |
| text_hash | Hash of normalized text content. |
| image_hash | Hash of source image bytes when available. |
| evidence_hash | Canonical hash of the complete evidence card. |
| quality_score | Numeric quality score for OCR/visual completeness. |
| quality_level | Human-readable quality level such as high, medium, low. |
| quality_reasons | Reasons for the assigned quality level. |

## 3. Implemented Fields

Current code paths already use `evidence_id`, `source_type`, `modality`, `visual_type`, `page`, `section`, `text`, `source_image_path`, `text_hash`, and `hash`/`evidence_hash`. These fields are consumed by visual retrieval, M-EPI inspection, GM audit payloads, provenance verification, and evidence bundle export.

## 4. Planned Enhancements

The planned card model adds `source_pdf`, `risk_tags`, `matched_keywords`, `image_hash`, `quality_score`, `quality_level`, and `quality_reasons`. These fields support explainable coverage reports, quality gates, and stronger source-level provenance.

## 5. Industrial visual_type Taxonomy

- `wiring_diagram`
- `terminal_layout`
- `module_front_panel`
- `diagnostic_alarm_page`
- `network_topology`
- `power_supply_installation`
- `parameter_table`
- `safety_warning_page`
- `model_order_number_page`
- `general_manual_page`

## 6. Hash And Provenance Fields

`text_hash`, `image_hash`, and `evidence_hash` provide tamper-evident anchors. `page`, `section`, `source_pdf`, and `source_image_path` provide human-verifiable provenance. In a full server deployment, the same `evidence_id` should be present in both the JSONL card file and the Visual Chroma collection.

## 7. Relation To M-EPI And SM3+SM2 Audit

M-EPI reads Evidence Cards to decide whether visual evidence is clean, real risk evidence, prompt injection, or poisoned evidence. The trusted multimodal query payload then records kept, quarantined, and risk evidence in an SM3+SM2 audit record. Evidence bundles export the audit record and card hashes for independent verification.

