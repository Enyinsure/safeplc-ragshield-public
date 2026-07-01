# Audit Chain Specification

Industrial safety RAG needs an audit chain because every answer may depend on retrieved evidence, risk decisions, and safety gates. A tamper-evident log lets reviewers reproduce what happened.

Each event records `event_id`, `timestamp`, `query`, `decision`, `risk_level`, `evidence_hashes`, `prev_hash`, `current_hash`, `signature_algorithm`, `signature_ok`, `key_id`, and `metadata`.

`prev_hash` links each event to the previous event. `current_hash` is computed from the stable event payload. If any earlier event is changed, verification fails at that event or the following link.

The `signature_algorithm` field is compatible with future SM2 integration. In this lightweight repository it is explicitly marked `SM2-compatible-demo`; it is not a real national-cryptography signature.

Limitations: without a real key-management module, the signature layer is a demo-compatible placeholder. The hash-chain tamper-detection logic is still useful for offline demonstrations and project reports.
