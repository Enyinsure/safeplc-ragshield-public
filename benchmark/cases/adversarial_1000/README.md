# adversarial_1000

Expanded 1000-case S7-RAGShield adversarial benchmark suite generated from local S7 text, table-like, and visual-card assets.

## Split

- `benign_control_100.jsonl`: 100 benign controls.
- `single_attack_650.jsonl`: 650 single-attack cases mapped to OWASP LLM01-LLM10.
- `mixed_attack_250.jsonl`: 250 mixed or multimodal attacks.
- `adversarial_1000_all.jsonl`: concatenated full suite.
- `manifest.json`: generation metadata and distribution summary.

The paired poison corpus is generated locally as `benchmark/poison_corpus/adversarial_1000_poison.jsonl`. It is intentionally not committed in the public tree because it may contain source-derived snippets.

## Generate

```bash
python3 benchmark/build_adversarial.py --suite adversarial_1000 --seed 20260629
```

The generator keeps source S7 materials read-only and writes all outputs under `benchmark/`.
