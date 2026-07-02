# Audit Chain Specification

Industrial safety RAG needs an audit chain because every answer may depend on retrieved evidence, risk decisions, and safety gates. A tamper-evident log lets reviewers reproduce what happened.

The current national-cryptography audit path is implemented in `safe/trusted_rag/multimodal_gm_sm2_audit_logger.py` and `safe/trusted_rag/audit_sm4_sealer.py`.

Each GM audit event records `timestamp`, `event_type`, `query`, retrieved evidence metadata, guard flags, policy action, output, `prev_hash`, `record_hash`, `hash_algorithm`, `signature_algorithm`, `sm2_public_key`, `sm2_signature`, and local sealing metadata returned by the logger.

## Integrity

- SM3: `record_hash` is computed from a canonical JSON body that includes query, evidence, policy action, output, signer metadata, and `prev_hash`.
- Hash chain: `prev_hash` links each event to the previous event in the same JSONL audit file. If any earlier record is changed, verification fails at that record or the following link.
- SM2: `record_hash` is signed with a local SM2 private key. Verification checks the SM2 signature and public-key fingerprint for every record.
- SM4: each audit JSONL file can be sealed as `*.jsonl.sm4.json` using SM4-CBC with PKCS7 padding. The sealed envelope stores SM3 digests for the envelope, plaintext, and ciphertext.

Local SM2 and SM4 keys are created under `safe/configs/gm_keys/`, which is ignored by Git. The public repository contains the implementation and verification tools, not private keys.

## Commands

```bash
python -m safe.trusted_rag.gm_crypto
python -m safe.trusted_rag.gm_sm2
python -m safe.trusted_rag.gm_sm4
python -m safe.trusted_rag.multimodal_gm_sm2_audit_logger
python -m safe.trusted_rag.audit_sm4_sealer --seal
python -m safe.trusted_rag.audit_sm4_sealer --verify safe/reports/audit_logs/audit_multimodal_gm_sm2_YYYYMMDD.jsonl.sm4.json
```

`append_gm_sm2_audit(...)` writes the plaintext JSONL record and then attempts to refresh the SM4 sealed copy for the same file. If sealing fails, the plaintext SM3+SM2 audit record remains valid and the returned logger metadata includes the sealing error.
