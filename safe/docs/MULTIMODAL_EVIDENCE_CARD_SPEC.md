# Multimodal Evidence Card Specification

SafePLC stores text, table, image, page, and OCR evidence in one normalized evidence-card structure. The required fields are:

- `evidence_id`: stable evidence identifier
- `source_file`: source document, image, table, or retrieval artifact
- `page_id`: page number or page-like identifier
- `modality`: `text`, `table`, `image`, `page`, or `ocr`
- `content`, `ocr_text`, `table_text`: modality-specific textual content
- `bbox`: optional visual bounding box
- `linked_text_chunks`: related text chunks from retrieval
- `risk_tags`: existing labels or scanner tags
- `source_hash`: deterministic card hash
- `is_real_risk_evidence`: true when a genuine manual warning should be preserved
- `is_poisoned`: true when the card is known or suspected poisoned
- `metadata`: implementation-specific details

The checker flags voltage conflicts, terminal-symbol ambiguity, safety-action contradictions, parameter-table anomalies, and visual/OCR prompt injection. Decisions are `keep`, `keep_as_risk_evidence`, `need_human_review`, or `quarantine`.
