# M-EPI Method Card

## Method Name

M-EPI: Multimodal Evidence Pollution Inspection.

## Motivation

Industrial RAG systems must use safety warnings as evidence while resisting malicious pollution in text chunks, OCR, figures, tables, and forged pages.

## Input And Output

Input is a normalized evidence card plus an optional query. Output is a total score, five subscores, a decision, a risk level, and human-readable reasons.

## Subscores

- `S_source`: source trust risk.
- `S_visual`: visual/OCR anomaly risk.
- `S_text`: prompt-injection risk.
- `S_consist`: text/table/image consistency risk.
- `S_action`: industrial action safety risk.

## Decision Rules

Real manual warnings without injection or conflict are kept as risk evidence. High-risk pollution is quarantined, medium-risk cases go to human review, low-risk evidence is kept, and dangerous operation queries are refused.

## Difference From Ordinary Filtering

SafePLC does not reject all dangerous content. It preserves genuine risk evidence such as warnings and hazardous wiring descriptions, while isolating malicious injection, forged evidence, and parameter tampering.

## Limitations

This lightweight implementation uses transparent rules and no large model. It should be validated against full server data and expanded with richer visual provenance checks later.
