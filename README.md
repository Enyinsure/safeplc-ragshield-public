# SafePLC Trusted RAG Codex Workspace

This is a lightweight workspace for implementing the trusted multimodal RAG security layer of SafePLC.

The full RAG vector database, raw S7 assets, model weights, runtime logs, and source-derived poison corpora are not included. This repo contains code, benchmark definitions, and small public-safe samples for development.

Main task: see `CODEX_TASK.md`.

## Frontend demo

Two public-safe frontend demos are available. They do not bundle private datasets,
model weights, runtime logs, server paths, tokens, private keys, vector indexes,
raw industrial manuals, or external competition images.

Streamlit security-chain demo:

```bash
streamlit run app_frontend.py --server.address 0.0.0.0 --server.port 8501
```

Static proposal dashboard:

```bash
python -m http.server 4173
```

Open `http://127.0.0.1:4173/frontend/`.

## Trusted RAG security layer

The trusted security layer lives under `safe/trusted_rag/` with a small CLI in `safe/secguard/demo_cli.py`. It adds offline path resolution, rule-based poison scanning, indirect prompt-injection checks, evidence consistency checks, risk-policy decisions, SM3/SM2/SM4 audit protection, hash-chain audit logs, integrity manifests, and red-team evaluation.

It does not require online APIs or full Chroma indexes in this lightweight repo. When the full Chroma paths are unavailable, retrieval falls back to the configured sample JSONL files.

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

## Adversarial Benchmark Quickstart

All benchmark-owned files live under `benchmark/`. The generators and runners do
not modify `safe/`, the production Chroma database, or original S7 materials.

### Build adversarial samples

Build the default expanded 1000-case suite from local S7 assets:

```bash
python3 benchmark/build_adversarial.py --suite adversarial_1000 --seed 20260629
```

Regenerate the original 500-case suite:

```bash
python3 benchmark/build_adversarial.py --suite adversarial_500 --seed 20260629
```

Generated outputs, which are intentionally ignored in the public tree:

- `benchmark/cases/adversarial_1000/adversarial_1000_all.jsonl`
- `benchmark/cases/adversarial_1000/benign_control_100.jsonl`
- `benchmark/cases/adversarial_1000/single_attack_650.jsonl`
- `benchmark/cases/adversarial_1000/mixed_attack_250.jsonl`
- `benchmark/poison_corpus/adversarial_1000_poison.jsonl`

### Offline evaluation

Offline evaluation uses the local benchmark adapter and guard modules. It does
not call Chroma, MinerU, Qwen, or any online API.

```bash
# Full 1000-case offline run.
python3 benchmark/run_adversarial_benchmark.py --suite adversarial_1000

# Small smoke-style subset.
python3 benchmark/run_adversarial_benchmark.py --suite adversarial_1000 --limit 25

# One case.
python3 benchmark/run_adversarial_benchmark.py --suite adversarial_1000 --case-id S1000_001
```

Offline outputs are written under `benchmark/results/<suite>/<timestamp>/` and
`benchmark/runtime/runs/<timestamp>/`. The offline adapter writes and verifies
SM3 hash-chain audit records for audit-required or blocked cases.

### Online evaluation

Online evaluation calls the configured project RAG path and requires a working
local environment: Chroma, BGE embedding model, and `safe/configs/local_paths.env`.
Use `--dry-run` first to check paths and dependencies.

```bash
# Preflight only.
python3 benchmark/run_online_benchmark.py --suite adversarial_1000 --dry-run

# Trusted RAG review chain enabled.
python3 benchmark/run_online_benchmark.py --suite adversarial_1000 --review-mode trusted --gateway off --poison-mode overlay
```

`--poison-mode overlay` appends benchmark poison evidence in memory for the
current evaluation call only. It does not write benchmark poison into the
production Chroma database.

To evaluate the full system with Qwen as the post-policy generator, keep the
trusted chain enabled and add `--generator qwen`:

```bash
python3 benchmark/run_online_benchmark.py \
  --suite adversarial_1000 \
  --review-mode trusted \
  --generator qwen \
  --gateway off \
  --poison-mode overlay
```

In this mode, BGE/Chroma retrieval, query scanning, evidence scanning, M-EPI,
risk policy, consistency checks, and audit logging run before Qwen is called.
Qwen receives only trusted evidence and is skipped when the policy returns
`refuse`, `safe_template`, or `clarify`.

For a pure local Qwen baseline with no Chroma/BGE retrieval and no trusted
review modules, set `SAFE_LLM_MODEL_DIR` in `safe/configs/local_paths.env` and
run:

```bash
python3 benchmark/run_online_benchmark.py \
  --suite adversarial_1000 \
  --review-mode qwen \
  --gateway off \
  --poison-mode overlay
```

In `qwen` mode, poison overlay means benchmark poison evidence is inserted
directly into the model prompt as unfiltered context. The strict `pass_rate`
still includes detector-flag expectations, while `behavior_pass_rate` ignores
missing detector flags and reflects model-only answer behavior.

### Audit-chain on/off comparison

Use the same suite, Chroma/BGE retrieval, and poison mode for both runs:

```bash
# Audit/review chain OFF: naive baseline, no trusted review and no project audit chain.
python3 benchmark/run_online_benchmark.py --suite adversarial_1000 --review-mode naive --gateway off --poison-mode overlay

# Audit/review chain ON: trusted review, risk policy, output filtering, and audit records.
python3 benchmark/run_online_benchmark.py --suite adversarial_1000 --review-mode trusted --gateway off --poison-mode overlay
```

Compare `attack_block_rate`, `poison_block_rate`, `canary_leak_count`,
`poison_citation_count`, and `audit_coverage` in the generated summaries.

For headline Trusted RAG results, keep `--gateway off` and avoid `--oracle-rules`;
`--gateway benchmark` and `--oracle-rules` are benchmark-owned upper-bound
diagnostics, not the project-chain result.
