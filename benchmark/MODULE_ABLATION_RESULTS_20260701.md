# SafePLC-RAGShield Module Ablation Results

This note summarizes the strict online module ablation run on 2026-07-01.

## Run Setting

- Repository commit: `c0f5ffb`
- Result root: `benchmark/results/module_ablation_20260701_154656`
- Runner: `benchmark/run_online_benchmark.py`
- Review mode: `trusted`
- Gateway: `off`
- Poison mode: `overlay`
- Oracle benchmark rules: `False`
- RAG calls: `500 / 500`
- Chroma cases: `500 / 500`
- Fallback cases: `0`

The run keeps the strict project-chain setting and disables one trusted-chain
module per ablation with `--disable-module`. It does not use the benchmark
gateway or oracle rules.

## Summary Table

| Setting | Disabled module | Passed / cases | Pass rate | Attack block | Poison block | Benign pass | Canary leaks | Poison citations |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Full Trusted RAG | none | 500 / 500 | 1.000 | 0.9600 | 1.0000 | 1.0000 | 0 | 0 |
| No Query Scan | `query_scan` | 322 / 500 | 0.644 | 0.6044 | 1.0000 | 1.0000 | 0 | 0 |
| No Evidence Scan | `evidence_scan` | 364 / 500 | 0.728 | 0.7267 | 0.5882 | 1.0000 | 0 | 0 |
| No Risk Policy | `risk_policy` | 305 / 500 | 0.610 | 0.5667 | 1.0000 | 1.0000 | 0 | 0 |
| No Combined Signal | `combined_signal` | 407 / 500 | 0.814 | 0.9600 | 1.0000 | 1.0000 | 0 | 0 |
| No Ingestion Gate | `ingestion_gate` | 493 / 500 | 0.986 | 0.9600 | 1.0000 | 1.0000 | 0 | 0 |
| No M-EPI | `mepi` | 493 / 500 | 0.986 | 0.9600 | 1.0000 | 1.0000 | 0 | 0 |
| No Visual Guard | `visual_guard` | 500 / 500 | 1.000 | 0.9600 | 1.0000 | 1.0000 | 0 | 0 |

All rows used `gateway=off`, `oracle_rules_enabled=False`,
`rag_called_count=500`, `chroma_case_count=500`, and `fallback_case_count=0`.

## Interpretation

The ablation results show that the 100% full-chain score is not caused by the
benchmark gateway or oracle rules. Disabling key project modules causes clear
performance drops:

- `query_scan` drops the pass rate from 100.0% to 64.4%, showing that
  query-side attack detection is a major contributor for single-input attacks.
- `evidence_scan` drops the pass rate to 72.8% and poison blocking to 58.82%,
  showing that evidence-side indirect injection and poisoning detection are
  central to the trusted RAG chain.
- `risk_policy` drops the pass rate to 61.0%, showing that detector flags must
  be enforced by refusal or safe-template decisions instead of merely being
  logged.
- `combined_signal` drops the pass rate to 81.4%, showing that multi-signal
  fusion is important for mixed and compound attacks.
- `ingestion_gate` and `mepi` each drop the pass rate to 98.6%, indicating
  measurable but partially redundant protection under this benchmark.
- `visual_guard` alone does not reduce the score in this run, which suggests
  that OCR/evidence scanning and M-EPI redundantly cover the current visual
  attack cases. This should be described as redundancy, not as evidence that the
  visual guard is unnecessary.

## Paper-Ready Claim

Under strict online scoring, SafePLC-RAGShield reaches 500/500 without using a
benchmark gateway or oracle rules. Module ablations reduce the pass rate to
64.4% without query scanning, 72.8% without evidence scanning, 61.0% without
risk-policy enforcement, and 81.4% without combined-attack fusion. These drops
indicate that the main safety gains come from query-side intent detection,
evidence-side poisoning detection, policy enforcement, and cross-signal fusion,
with multimodal modules providing additional redundant protection.
