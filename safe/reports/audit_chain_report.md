# SafePLC Audit Chain Report

## Audit Fields

- `event_id`: stable event identifier
- `timestamp`: event time
- `query`: user or evaluation query
- `decision`: trusted decision such as answer, quarantine, or refuse
- `risk_level`: low, medium, or high
- `evidence_hashes`: hashes of evidence used by the decision
- `prev_hash` / `current_hash`: hash-chain links
- `signature_algorithm`: `SM2-compatible-demo` in this lightweight implementation
- `signature_ok`: demo signature verification status
- `key_id`: key identifier for later real SM2 integration

## Verification Result

- OK: True
- Event count: 3
- Root hash: `c764a291f58f576e95dc0709fc97e9271fe390be3dbd9ea06128f3909eca0f3f`
- Tamper detected: False
- Signature algorithm: SM2-compatible-demo

## Errors

- None

## Event Summary

| Event | Decision | Risk | Evidence Hashes |
|---|---|---|---:|
| evt_query_001 | answer | low | 1 |
| evt_mepi_002 | quarantine | high | 1 |
| evt_redteam_003 | need_human_review | medium | 1 |

## Project-Book Conclusion

The audit chain makes each SafePLC trusted-RAG decision reproducible and tamper-evident. Every event links to the previous hash, records the evidence hashes used by the decision, and reserves signature metadata for a later real SM2/SM3 key-management layer. In this lightweight repository the signature is explicitly marked as a demo-compatible placeholder.

## Tamper Demo

- Original verification OK: True
- Tampered verification OK: False
- Tamper detected: True
- Tamper errors: evt_mepi_002: current_hash mismatch
