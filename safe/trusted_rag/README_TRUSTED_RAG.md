# SafePLC Trusted RAG Security Layer

This folder adds an offline trusted security layer around the existing SafePLC multimodal RAG code. It does not rewrite the old RAG modules and does not require the full Chroma indexes during lightweight development.

## Architecture

The pipeline is implemented in `trusted_query.py`:

1. Create a `query_id`.
2. Scan the user query with `poison_scanner.py`.
3. Retrieve evidence from Chroma when available, otherwise from the configured sample JSONL files.
4. Convert results to `EvidenceRecord` objects.
5. Scan evidence for indirect prompt injection with `indirect_prompt_guard.py`.
6. Generate a conservative evidence-summary answer.
7. Check answer support with `consistency_checker.py`.
8. Apply `risk_policy.py`.
9. Write a hash-chain audit event through `audit_logger.py`.
10. Return a `TrustedAnswer`.

## Modules

- `paths.py`: loads `safe/configs/local_paths.env`, resolves paths from the repo root, and creates runtime report directories.
- `evidence_schema.py`: dataclasses for evidence, retrieval traces, decisions, and trusted answers.
- `hash_chain.py`: deterministic SHA-256 helpers plus append/verify support for JSONL audit chains.
- `audit_logger.py`: writes `safe/reports/audit_logs/audit_YYYYMMDD.jsonl`.
- `gm_crypto.py`: pure Python SM3 helpers and canonical JSON hashing.
- `gm_sm2.py`: local SM2 key generation, digest signing, and verification.
- `gm_sm4.py`: pure Python SM4 block cipher and SM4-CBC helpers.
- `multimodal_gm_sm2_audit_logger.py`: SM3+SM2 multimodal audit records with `prev_hash` and `record_hash`.
- `audit_sm4_sealer.py`: SM4-CBC local sealing and verification for audit JSONL files.
- `integrity_checker.py`: creates and verifies data manifests under `safe/reports/manifests`.
- `poison_scanner.py`: Chinese/English rule scanner for prompt injection, fake authorization, safety bypass, and dangerous PLC actions.
- `trusted_query.py`: offline trusted-answer pipeline.
- `redteam_eval.py`: executes `safe/tests/redteam_cases.jsonl` and writes JSON/Markdown reports.

## Threat Model

The layer targets direct prompt injection, indirect prompt injection inside retrieved chunks, fake authority claims, unsupported answer claims, weak/no evidence, and dangerous PLC operations such as forcing outputs, bypassing interlocks, disabling protection, or modifying a live controller.

## Relation To Existing RAG

Existing modules in `safe/core_rag/` and `safe/core_rag_multimodal/` are left intact. This layer is a conservative wrapper that can use full Chroma later, but it can run offline in the lightweight package using the sample JSONL files.

## Lightweight Repo Limitation

The full text/table and figure Chroma indexes are not included. In this environment, integrity manifests will record those paths as missing if they are not mounted. Retrieval then falls back to:

- `s7_full_chunks.sample.jsonl`
- `s7_full_pages.sample.jsonl`

These paths are configured in `safe/configs/local_paths.env`.

## Full Server Validation

On the school server, set or edit:

- `SAFE_CHROMA_DIR=~/s7_chroma_db_v3_tables`
- `SAFE_FIGURE_CHROMA_DIR=~/s7_multimodal_v1/index/chroma_figures_v1`
- `SAFE_CHUNKS_JSONL=<full-or-sample-chunks-jsonl>`
- `SAFE_PAGES_JSONL=<full-or-sample-pages-jsonl>`

Then run the same commands below. If `chromadb` is installed and the Chroma directory exists, `trusted_query.py` will use Chroma; otherwise it falls back gracefully.

## Commands

```bash
python -m safe.trusted_rag.paths
python -m safe.trusted_rag.integrity_checker
python -m safe.trusted_rag.redteam_eval
python -m safe.trusted_rag.gm_crypto
python -m safe.trusted_rag.gm_sm2
python -m safe.trusted_rag.gm_sm4
python -m safe.trusted_rag.multimodal_gm_sm2_audit_logger
python -m safe.trusted_rag.audit_sm4_sealer --seal
python -m safe.secguard.demo_cli "S7-1500 CPU 故障灯亮应该如何排查？"
```

Shell wrappers:

```bash
bash safe/scripts/run_trusted_rag_integrity_check.sh
bash safe/scripts/run_trusted_rag_redteam.sh
```
