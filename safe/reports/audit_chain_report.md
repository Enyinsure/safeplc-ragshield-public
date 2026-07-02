# SafePLC Audit Chain Report

## Audit Fields

- `event_id`: stable event identifier
- `timestamp`: event time
- `query`: user or evaluation query
- `decision`: trusted decision such as answer, quarantine, or refuse
- `risk_level`: low, medium, or high
- `evidence_hashes`: hashes of evidence used by the decision
- `prev_hash` / `current_hash`: hash-chain links
- `signature_algorithm`: legacy demo signature marker for this compatibility report
- `signature_ok`: legacy demo signature verification status
- `key_id`: local demo key identifier

## Verification Result

- OK: True
- Event count: 3
- Root hash: `75c8e6ad3b87f222423cb5fe481a66d99e013f26b3cd7512bb9a09c2742ef282`
- Tamper detected: False
- Signature algorithm: legacy-sha256-demo

## Errors

- None

## Event Summary

| Event | Decision | Risk | Evidence Hashes |
|---|---|---|---:|
| evt_query_001 | answer | low | 1 |
| evt_mepi_002 | quarantine | high | 1 |
| evt_redteam_003 | need_human_review | medium | 1 |

## Project-Book Conclusion

The audit chain makes each SafePLC trusted-RAG decision reproducible and tamper-evident. Every event links to the previous hash, records the evidence hashes used by the decision, and records legacy demo signature metadata for backwards-compatible reports. For the formal national-cryptography path, use the SM3+SM2+SM4 modules under `safe/trusted_rag/`.

## Tamper Demo

- Original verification OK: True
- Tampered verification OK: False
- Tamper detected: True
- Tamper errors: evt_mepi_002: current_hash mismatch
