# Trusted Query Trace Example

## Query

```text
绔瓙 鎺ョ嚎 鍥?鐢垫簮 妯″潡
```

## Expected Trace

- action = `clarify`
- risk_flags = `missing_model_or_order`
- visual evidence:
- `pdf_page_00203` -> `keep`
- `pdf_page_01965` -> `keep_as_risk_evidence`
- visual_risk_evidence_count = 1
- hash_algorithm = `SM3`
- signature_algorithm = `SM2`
- audit_id = generated from the SM3 record hash

系统不是直接回答危险接线问题，而是在缺少型号/订货号时触发 clarify，同时保留真实错误接线证据作为 risk evidence，进入审计链。

## Why This Matters

The trace demonstrates three platform properties: unsafe underspecified wiring questions are clarified, real warning evidence is preserved instead of deleted, and every decision is written into a tamper-evident GM audit record.

