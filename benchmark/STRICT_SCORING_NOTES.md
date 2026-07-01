# Strict Online Benchmark Scoring Notes

Use this command for the main Trusted RAG result:

```bash
python3 benchmark/run_online_benchmark.py \
  --review-mode trusted \
  --gateway off \
  --poison-mode overlay
```

Use this command for the full product-style chain with Qwen generation behind
the trusted policy:

```bash
python3 benchmark/run_online_benchmark.py \
  --review-mode trusted \
  --generator qwen \
  --gateway off \
  --poison-mode overlay
```

This setting keeps the comparison clean:

- the project trusted RAG chain is enabled;
- the benchmark input gateway is disabled;
- benchmark-owned query/evidence oracle rules are not added to scoring;
- RAG should still be called for every case when Chroma/BGE is configured;
- with `--generator qwen`, Qwen is called only for trusted `action=answer`
  cases and receives only post-scan trusted evidence;
- poison evidence is overlaid in memory and production Chroma is not modified.

Do not report these modes as the headline Trusted RAG result:

- `--gateway benchmark`: blocks with benchmark-owned query rules before RAG.
- `--oracle-rules`: adds benchmark-owned `QUERY_RULES` and `EVIDENCE_RULES` to scoring.
- `benchmark/safeplc_adapter.py`: offline guard adapter; useful for module smoke tests, not for end-to-end Chroma/BGE Trusted RAG claims.
- `--review-mode qwen`: pure local LLM baseline. It does not call Chroma/BGE
  retrieval or any trusted review module, and should be reported separately
  from RAG-chain results.
- `--poison-mode none`: a no-overlay diagnostic. It is not a true module
  ablation because the trusted chain is still enabled.

For module ablations, keep the strict setting and add exactly one repeated
`--disable-module` target per run unless deliberately studying interactions:

- `--disable-module query_scan`
- `--disable-module evidence_scan`
- `--disable-module ingestion_gate`
- `--disable-module mepi`
- `--disable-module visual_guard`
- `--disable-module combined_signal`
- `--disable-module risk_policy`

Each run records the active ablation list in `disabled_modules`.

If a run reports 100% pass rate, inspect these fields before trusting it:

- `gateway`
- `oracle_rules_enabled`
- `disabled_modules`
- `gateway_block_count`
- `rag_called_count`
- `chroma_case_count`
- `fallback_case_count`
- per-case `query_gateway.mode`
- per-case `raw_action`
- per-case `normalised_action`

A credible online comparison should state both `passed / case_count` and the exact runner options.
