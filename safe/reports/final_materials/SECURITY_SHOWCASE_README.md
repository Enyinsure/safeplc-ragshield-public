# Security Showcase README

Run the showcase from a fresh clone with:

```bash
python -m safe.secguard.demo_security_showcase
```

The expected output includes:

```text
clean evidence -> keep
risk visual evidence -> keep_as_risk_evidence
visual prompt injection -> quarantine
poisoned evidence -> quarantine
SM3+SM2 audit -> valid
tampered audit -> detected
SHOWCASE_PASS = True
```

Additional verification commands:

```bash
python -m safe.trusted_rag.eval_multimodal_poison_guard --cases safe/tests/mepi_visual_guard_cases.jsonl --out_csv safe/reports/mepi_visual_guard_eval.csv --summary_json safe/reports/mepi_visual_guard_eval_summary.json
python -m safe.trusted_rag.eval_multimodal_poison_guard --cases safe/tests/mepi_visual_guard_cases_100.jsonl --out_csv safe/reports/mepi_visual_guard_eval_100.csv --summary_json safe/reports/mepi_visual_guard_eval_100_summary.json
python -m safe.trusted_rag.gm_crypto
python -m safe.trusted_rag.gm_sm2
python -m safe.trusted_rag.multimodal_gm_sm2_audit_logger
python -m safe.trusted_rag.tamper_test_gm_sm2_audit
python -m safe.trusted_rag.build_final_security_report
```

Generated keys, audit logs, CSV summaries, and final timestamped reports are local runtime artifacts and should not be committed.
