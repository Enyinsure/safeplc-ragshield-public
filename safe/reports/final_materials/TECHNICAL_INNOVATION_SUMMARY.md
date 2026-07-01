# Technical Innovation Summary

SafePLC-RAGShield builds a multimodal industrial evidence chain for trusted RAG. Visual, OCR, table, and text evidence are normalized, hashed, inspected, and audited before they can influence the final answer.

The M-EPI visual guard separates four cases:

- clean evidence is kept;
- genuine risk visual evidence is preserved as `keep_as_risk_evidence`;
- visual prompt injection is quarantined;
- forged or poisoned evidence is quarantined.

This distinction matters for industrial safety: real manual warnings, diagnostic diagrams, alarm descriptions, and wiring risk evidence must remain available, while prompt injection and forged safety claims must be isolated.

The audit layer adds SM3 record hashing, SM2 signatures, hash-chain linkage, and tamper detection. The implementation is pure Python and designed for offline server validation without online APIs or large-model dependencies.
