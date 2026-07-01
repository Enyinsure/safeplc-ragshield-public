# Local Poison Corpus

The generated poison corpus JSONL files are intentionally not committed.

These files may contain source-derived S7 text/table/visual snippets and local
asset metadata. Generate them in the private/server environment before running
strict overlay benchmarks.

Expected generated files include:

- `adversarial_500_poison.jsonl`
- `adversarial_1000_poison.jsonl`
- `near_duplicate_poison.jsonl`
- `near_duplicate_poison.stats.json`
