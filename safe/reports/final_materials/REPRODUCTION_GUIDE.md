# Reproduction Guide

## Environment

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate s7rag_ui
export PYTHONPATH=$PWD:$PYTHONPATH
```

The code is offline and does not require online APIs or LLM calls.

## Configure `local_paths.env`

Copy the example file in a private clone:

```bash
cp safe/configs/local_paths.example.env safe/configs/local_paths.env
```

Fill in real server paths only in the private clone:

```env
SAFE_ROOT=
SAFE_VISUAL_CARDS_V2=
SAFE_VISUAL_CHROMA_DIR_V2=
SAFE_VISUAL_COLLECTION_V2=s7_visual_cards_v2
SAFE_AUDIT_DIR=safe/reports/audit_logs
SAFE_FINAL_REPORT_DIR=safe/reports
```

## Files That Must Not Be Committed

- `safe/configs/local_paths.env`
- `safe/configs/gm_keys/`
- `safe/reports/audit_logs/`
- `safe/reports/audit_bundles/`
- real PDFs, images, Chroma DB files, CSV outputs, generated final reports

## Run Full Chain Validation

```bash
python -m safe.secguard.run_full_final_validation
python -m safe.trusted_rag.build_final_security_report
```

## Core Single Commands

```bash
python -m safe.multimodal_guard.build_visual_db_coverage_report
python -m safe.multimodal_guard.verify_visual_evidence_provenance --evidence_id pdf_page_01965

python -m safe.trusted_rag.eval_multimodal_poison_guard \
  --cases safe/tests/mepi_visual_guard_cases_100.jsonl \
  --out_csv safe/reports/mepi_visual_guard_eval_100.csv \
  --summary_json safe/reports/mepi_visual_guard_eval_100_summary.json

python -m safe.secguard.demo_multimodal_cli "绔瓙 鎺ョ嚎 鍥?鐢垫簮 妯″潡" --visual_n 2

python -m safe.trusted_rag.export_evidence_bundle --latest
python -m safe.trusted_rag.verify_evidence_bundle --latest
python -m safe.trusted_rag.audit_tamper_matrix
python -m safe.trusted_rag.build_gm_audit_validation_report

python -m safe.secguard.demo_security_showcase
```

## Expected Output

- M-EPI smoke: `total=8`, `correct=8`, `accuracy=1.0`
- M-EPI-100: `total=100`, `correct=100`, `accuracy=1.0`
- `pdf_page_01965 -> keep_as_risk_evidence`
- SM3: `self_test=True`
- SM2: `self_test=True`
- Audit: `hash_chain_ok=True`, `sm2_signature_ok=True`
- Tamper: `tamper_detected=True`
- Bundle: `result=PASS`
- Showcase: `SHOWCASE_PASS=True`
- Full validation: `FINAL_VALIDATION_PASS=True`

## Common Warnings

Fresh GitHub clones do not include the real Visual DB, Chroma index, images, or PDFs. Coverage and provenance commands can return WARN in that environment. After `local_paths.env` points to the real server assets, those checks should become stronger PASS-level evidence.

