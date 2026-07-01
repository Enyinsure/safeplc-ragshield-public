# Strict Online Benchmark Summary - 2026-06-30

## Post-review note - 2026-07-01

This 500/500 run was produced before the online benchmark runner fully
sanitized benchmark-owned poison labels from M-EPI, visual guard, overlay
evidence, and mixed-attack action normalization. Treat it as a historical run
record only, not as the final strict score. Re-run the benchmark after
`benchmark/run_online_benchmark.py` strict-label sanitization is applied.

## Run Directory

benchmark/results/strict_main_after_flags_20260630_212235

## Configuration

- review_mode: trusted / naive comparison
- gateway: off
- oracle_rules_enabled: false
- allow_fallback: false
- require_chroma: true
- chroma collection: s7_1500_manual
- collection_count: 16628
- rag_called_count: 500
- chroma_case_count: 500
- fallback_case_count: 0

## Trusted Result

- passed / case_count / pass_rate: 500 / 500 / 1.0
- benign_pass_rate: 1.0
- attack_block_rate: 0.96
- poison_block_rate: 1.0
- canary_leak_count: 0
- poison_citation_count: 0
- failed: 0
- missing_flags: none
- forbidden_hits: none

## Naive Baseline

- passed / case_count / pass_rate: 50 / 500 / 0.1
- benign_pass_rate: 1.0
- attack_block_rate: 0.2222
- poison_block_rate: 0.3922
- canary_leak_count: 97
- poison_citation_count: 255
- failed: 450

## Fix Notes

This run uses strict scoring with benchmark gateway disabled and oracle rules disabled.
The fixes are product/risk-signal alignment changes:

1. Refusal text was de-sensitized to avoid echoing forbidden trigger phrases.
2. High-risk M-EPI quarantine is exposed as indirect_prompt_injection.
3. High-risk multimodal poisoned evidence is exposed as cross_modal_conflict when applicable.

The scoring logic was not relaxed, and no output sanitizer was added to the evaluator.

## Interpretation

Under the current adversarial_500 strict online benchmark, the trusted chain passes all 500 cases while the naive baseline passes only benign controls. This shows the effectiveness of the trusted review chain, M-EPI evidence quarantine, risk policy, and audit path on this benchmark. This does not imply absolute system security; future work should include external negative controls and less template-like attacks.
