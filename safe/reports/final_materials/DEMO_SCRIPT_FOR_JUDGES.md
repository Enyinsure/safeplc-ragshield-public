# Demo Script For Judges

## 1. Input A Terminal Wiring Question

Run:

```bash
python -m safe.secguard.demo_multimodal_cli "绔瓙 鎺ョ嚎 鍥?鐢垫簮 妯″潡" --visual_n 2
```

Expected behavior: the system asks for exact model/order number instead of giving unsafe wiring instructions.

## 2. Show Clarification

Point out `action: clarify` and `risk_flags: ['missing_model_or_order']`.

## 3. Show Visual Evidence

Use the provenance command for `pdf_page_01965`:

```bash
python -m safe.multimodal_guard.verify_visual_evidence_provenance --evidence_id pdf_page_01965
```

In a fresh clone this may WARN because the real Visual DB is not included. On the server it should link to the card, page, section, image, and Chroma record.

## 4. Explain M-EPI Decision

`pdf_page_01965` is real risk evidence, so M-EPI preserves it as `keep_as_risk_evidence` instead of quarantining it.

## 5. Show SM3/SM2 Audit Record

Run:

```bash
python -m safe.trusted_rag.multimodal_gm_sm2_audit_logger
```

Expected: `hash_chain_ok = True`, `sm2_signature_ok = True`.

## 6. Export Evidence Bundle

```bash
python -m safe.trusted_rag.export_evidence_bundle --latest
```

## 7. Verify Offline

```bash
python -m safe.trusted_rag.verify_evidence_bundle --latest
```

Expected: `result = PASS`.

## 8. Tamper And Verify Failure

```bash
python -m safe.trusted_rag.audit_tamper_matrix
```

Expected: every tamper field is detected and `matrix_pass = True`.

## 9. Show Final Report

```bash
python -m safe.trusted_rag.build_final_security_report
```

The generated report is local runtime output and should not be committed.

