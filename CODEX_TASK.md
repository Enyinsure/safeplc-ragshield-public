# SafePLC Trusted Multimodal RAG Security Framework

You are working on a lightweight private GitHub repo for the SafePLC RAG project.

Do not upload, require, or generate large database files. Do not depend on online APIs. Only add or modify code under `safe/`.

## Server-side full database status

The full database is NOT included in this repo. It exists on the school server:

- Main text/table Chroma DB: `~/s7_chroma_db_v3_tables`
- Main collection: `s7_1500_manual`
- Main count: 16628
- Figure Chroma DB: `~/s7_multimodal_v1/index/chroma_figures_v1`
- Figure collection: `s7_figures_v1`
- Figure count: 37

## Lightweight files included

- `safe/`: existing project code
- `db_schema_only/DB_SUMMARY.md`: lightweight database summary only
- `s7_full_chunks.sample.jsonl`: JSONL sample
- `s7_full_pages.sample.jsonl`: JSONL sample

## Existing modules

- `safe/core_rag/`
- `safe/core_rag_multimodal/`
- `safe/build_index/`
- `safe/existing_reports/`
- `safe/existing_scripts/`
- `safe/core_rag/safety_guard_v1.py`
- `safe/core_rag/ask_s7_multimodal_final_safety.py`
- `safe/core_rag_multimodal/app_streamlit_safety.py`

## Required implementation

Add a trusted RAG security layer:

1. `safe/trusted_rag/paths.py`
2. `safe/trusted_rag/evidence_schema.py`
3. `safe/trusted_rag/hash_chain.py`
4. `safe/trusted_rag/audit_logger.py`
5. `safe/trusted_rag/integrity_checker.py`
6. `safe/trusted_rag/poison_scanner.py`
7. `safe/trusted_rag/indirect_prompt_guard.py`
8. `safe/trusted_rag/consistency_checker.py`
9. `safe/trusted_rag/risk_policy.py`
10. `safe/trusted_rag/trusted_query.py`
11. `safe/trusted_rag/redteam_eval.py`
12. `safe/secguard/demo_cli.py`
13. `safe/tests/redteam_cases.jsonl`
14. `safe/scripts/run_trusted_rag_integrity_check.sh`
15. `safe/scripts/run_trusted_rag_redteam.sh`
16. `safe/trusted_rag/README_TRUSTED_RAG.md`

## Functional requirements

- Use `safe/configs/local_paths.env` or `safe/trusted_rag/paths.py` for all paths.
- Write all reports under `safe/reports`.
- Write all security events into hash-chain audit logs.
- Support graceful fallback when full Chroma vector index is missing.
- `trusted_answer(query: str)` should run:
  query risk scan -> retrieval/fallback evidence -> evidence structuring -> indirect prompt detection -> consistency check -> risk policy -> audit log -> TrustedAnswer.
- Provide offline red-team evaluation with at least 20 cases.
- Provide CLI:
  `python -m safe.secguard.demo_cli "S7-1500 CPU 故障灯亮应该如何排查？"`

## Constraints

- Offline only.
- No online API.
- No destructive file operation.
- Do not move/delete old files.
- Do not require full vector database or sqlite database files in this lightweight repo.
- Final code must be testable on the full server database later.
