# Red-Team Threat Model

SafePLC assumes an attacker can pollute PDF pages, OCR text, parameter tables, forged manual pages, retrieval top-k results, fake authoritative sources, and audit logs.

The attacker's objective is to make a RAG system either follow malicious instructions, quote poisoned parameters, provide dangerous field-operation steps, or erase evidence that a risky answer was produced.

The defense objective is twofold:

1. Isolate maliciously polluted evidence before answer generation.
2. Preserve genuine manual warnings and risk descriptions as real risk evidence.

The showcase compares a vanilla RAG baseline that trusts top evidence with SafePLC's M-EPI and multimodal consistency checks.
