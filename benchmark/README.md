# S7-RAGShield Adversarial Benchmark

This folder contains the imported adversarial benchmark for the SafePLC/S7
trusted RAG project.  The public tree keeps case definitions, generators,
adapter code, and benchmark documentation. Source-derived poison corpora,
runtime logs, and raw reports are generated locally and ignored by Git.

It intentionally keeps all benchmark-owned files under `benchmark/` and does not modify:

- `safe/`
- existing Chroma databases
- existing SafePLC module interfaces

## What It Covers

The suite covers two orthogonal axes:

- Attack complexity: `benign`, `single_attack`, and `multi_attack`
- Modality complexity: `single_modal` and `multimodal`

Main tracks:

- `benign_control`
- `direct_prompt_injection`
- `indirect_injection`
- `retrieval_poisoning`
- `vector_embedding_weakness`
- `sensitive_disclosure`
- `improper_output_handling`
- `excessive_agency`
- `system_prompt_leakage`
- `supply_chain_spoof`
- `technical_misinformation`
- `unbounded_consumption`
- `mixed_qa`
- `multi_attack`

## Run

From the repository root:

```bash
python3 benchmark/run_adversarial_benchmark.py
```

Run only a small static smoke subset:

```bash
python3 benchmark/run_adversarial_benchmark.py --limit 25
```

Run one case:

```bash
python3 benchmark/run_adversarial_benchmark.py --case-id S500_001
```

Build the expanded 1000-case suite from local S7 assets:

```bash
python3 benchmark/build_adversarial.py --suite adversarial_1000 --seed 20260629
```

Run the expanded 1000-case suite offline:

```bash
python3 benchmark/run_adversarial_benchmark.py --suite adversarial_1000
```

Run the online benchmark through the configured trusted RAG path:

```bash
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay
```

Run the expanded 1000-case suite online:

```bash
python3 benchmark/run_online_benchmark.py --suite adversarial_1000 --review-mode trusted --gateway off --poison-mode overlay
```

Run a before/after comparison of the RAG review chain:

```bash
# Before review: same Chroma/BGE retrieval, no trusted review, no audit chain.
python3 benchmark/run_online_benchmark.py --review-mode naive --gateway off --poison-mode overlay

# After review: same Chroma/BGE retrieval, project trusted review and audit chain.
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay
```

Use these two runs to compare `attack_block_rate`, `poison_block_rate`,
`canary_leak_count`, `poison_citation_count`, and `audit_coverage`.

Run the full trusted chain with Qwen as the post-policy generator:

```bash
# Full chain: Chroma/BGE retrieval, trusted review modules, risk policy,
# post-generation consistency check, audit chain, then Qwen only for allowed answers.
# SAFE_LLM_MODEL_DIR can point to Qwen2.5-VL-3B-Instruct or Qwen2.5-VL-7B-Instruct.
python3 benchmark/run_online_benchmark.py \
  --suite adversarial_1000 \
  --review-mode trusted \
  --generator qwen \
  --gateway off \
  --poison-mode overlay
```

In `trusted --generator qwen` mode, Qwen is not a bypass. It is called only
after the trusted chain returns `action=answer`, and the prompt contains only
trusted evidence that survived project scanning. Policy refusals, safe
templates, and clarifications do not call Qwen.

Run a pure Qwen2.5-VL baseline without Chroma/BGE retrieval or trusted review
modules:

```bash
# First set SAFE_LLM_MODEL_DIR in safe/configs/local_paths.env, for example:
# SAFE_LLM_MODEL_DIR=models/Qwen/Qwen2.5-VL-7B-Instruct
python3 benchmark/run_online_benchmark.py \
  --suite adversarial_1000 \
  --review-mode qwen \
  --gateway off \
  --poison-mode overlay
```

In `qwen` mode, `--poison-mode overlay` places benchmark poison evidence
directly into the model prompt as unfiltered context. It does not call Chroma,
BGE, the trusted review chain, the input gateway, the ingestion gate, M-EPI,
the risk policy, or the audit logger. Use `behavior_pass_rate` to inspect
model-only behavior separately from strict detector-flag scoring.

Audit-chain on/off commands for the expanded 1000-case suite:

```bash
# OFF: naive baseline. It bypasses trusted review, risk policy, output filter,
# and the project audit chain while keeping the same Chroma/BGE retrieval path.
python3 benchmark/run_online_benchmark.py --suite adversarial_1000 --review-mode naive --gateway off --poison-mode overlay

# ON: trusted path. It enables project trusted review and audit records.
python3 benchmark/run_online_benchmark.py --suite adversarial_1000 --review-mode trusted --gateway off --poison-mode overlay
```

For a clean audit-chain comparison, keep `--gateway off` in both commands.
`--gateway benchmark`, `--gateway project`, and `--oracle-rules` are useful for
diagnostics or ablations, but they change what is being measured.

Run true module ablations by keeping the strict online setting and disabling one
trusted-chain module at a time:

```bash
# Full trusted chain / headline setting.
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay

# Query-side detector ablation.
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay --disable-module query_scan

# Evidence/indirect-poisoning detector ablation.
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay --disable-module evidence_scan

# Pre-index ingestion gate ablation.
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay --disable-module ingestion_gate

# Multimodal consistency ablations.
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay --disable-module mepi
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay --disable-module visual_guard

# Combined-attack fusion and policy-enforcement ablations.
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay --disable-module combined_signal
python3 benchmark/run_online_benchmark.py --review-mode trusted --gateway off --poison-mode overlay --disable-module risk_policy
```

Every ablation run records `disabled_modules` in `preflight.json`,
`summary.json`, and per-case results.  `--poison-mode none` is not a module
ablation; it only disables in-memory poison overlay and should be reported as a
clean/no-overlay diagnostic.

Recorded strict online module ablation results are summarized in
[`MODULE_ABLATION_RESULTS_20260701.md`](MODULE_ABLATION_RESULTS_20260701.md).

Important scoring note:

- `--gateway off` is the strict project-chain setting for the headline result.
- `--gateway project` measures a project input-gateway ablation before RAG and
  should be reported separately because it may reduce `rag_called_count`.
- `--gateway benchmark` and `--oracle-rules` use benchmark-owned detector rules.
  They are useful only as oracle/upper-bound diagnostics and must not be
  reported as the main Trusted RAG result.
- A suspicious 100% pass rate usually means the benchmark gateway or oracle
  rules were enabled, not that the end-to-end RAG review chain became perfect.

Online preflight only:

```bash
python3 benchmark/run_online_benchmark.py --dry-run
```

Online runner poison modes:

- `--poison-mode overlay`: default; run real retrieval first, then append poison
  evidence in memory for this benchmark call only. Production Chroma is not
  modified.
- `--poison-mode ingest-only`: only test whether poison evidence is blocked
  before indexing.
- `--poison-mode none`: do not inject benchmark poison evidence.

By default, the online runner requires a configured real Chroma collection. Use
`--allow-fallback` only when intentionally testing the sample JSONL fallback.

Outputs are written only under:

- `benchmark/results/adversarial_500/<timestamp>/`
- `benchmark/results/adversarial_1000/<timestamp>/`
- `benchmark/results/online_adversarial_500/<timestamp>/`
- `benchmark/results/online_naive_adversarial_500/<timestamp>/`
- `benchmark/results/online_adversarial_1000/<timestamp>/`
- `benchmark/results/online_naive_adversarial_1000/<timestamp>/`
- `benchmark/runtime/runs/<timestamp>/`
- `benchmark/runtime/online_runs/<timestamp>/`

The adapter reuses the existing `safe.trusted_rag` modules from this repository
root.  It redirects SafePLC audit/report environment variables into a per-run
folder under `benchmark/runtime/runs/` before importing those modules.

## Files

- `cases/smoke_cases.jsonl`: benchmark case definitions.
- `cases/adversarial_500/adversarial_500_all.jsonl`: full 500-case suite.
- `cases/adversarial_500/benign_control_050.jsonl`: 50 benign controls.
- `cases/adversarial_500/single_attack_350.jsonl`: 350 single-attack cases.
- `cases/adversarial_500/mixed_attack_100.jsonl`: 100 mixed/multimodal cases.
- `cases/adversarial_1000/adversarial_1000_all.jsonl`: expanded 1000-case suite with harder prompt variants and exact prompt de-duplication.
- `cases/adversarial_1000/benign_control_100.jsonl`: 100 benign controls.
- `cases/adversarial_1000/single_attack_650.jsonl`: 650 single-attack cases.
- `cases/adversarial_1000/mixed_attack_250.jsonl`: 250 mixed/multimodal cases.
- `poison_corpus/`: local-only generated poison evidence. The full JSONL corpora are not committed because they may contain source-derived snippets.
- `safeplc_adapter.py`: offline adapter from benchmark JSONL to SafePLC guard modules.
- `run_adversarial_benchmark.py`: CLI entry point for the imported 500-case suite.
- `run_online_benchmark.py`: online runner that supports both naive pre-review and trusted post-review modes, using the configured Chroma/BGE path and in-memory poison overlay.
- `MODULE_ABLATION_RESULTS_20260701.md`: strict online module ablation summary from the 2026-07-01 server run.
- `build_near_duplicate_poison.py`: reads real S7 text/table/visual assets and writes near-duplicate synthetic poison samples under `benchmark/poison_corpus/`.
- `build_adversarial.py`: generates the formal 500-case and expanded 1000-case suites split into benign, single-attack, and mixed-attack files.
- `run_smoke_benchmark.py`: offline runner and metric reporter.

## Notes

- Poison samples use synthetic canaries such as `SAFEPLC_BENCH_500_S500_001` and `SAFEPLC_BENCH_1000_S1000_001`.
- `safeplc_adapter.py` is an offline guard baseline. It does not call Chroma,
  MinerU, or Qwen; it validates input/evidence guards, M-EPI, visual quarantine,
  and SM3 hash-chain audit logging.
- Full strict benchmark runs require the locally generated poison corpus for
  the selected suite. Generate it on the server from local S7 assets before
  running `--poison-mode overlay`.
- The generation scripts require access to the original real S7 asset folders.
  Case definitions can be inspected without those source assets.
- No real secrets or personal data are used.
