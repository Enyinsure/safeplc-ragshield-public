# M-EPI Showcase Report

## Formula

`M_EPI = 0.20*S_source + 0.20*S_visual + 0.20*S_text + 0.20*S_consist + 0.20*S_action`.

## Subscores

- `S_source`: source trust risk
- `S_visual`: visual/OCR anomaly risk
- `S_text`: prompt-injection text risk
- `S_consist`: image/text/table consistency risk
- `S_action`: industrial action safety risk

## Decision Classes

`keep`, `keep_as_risk_evidence`, `quarantine`, `need_human_review`, and high-risk query `refuse`.

## Demo Score Table

| Case | Score | Decision | Risk | Subscores |
|---|---:|---|---|---|
| clean evidence | 0.01 | keep | low | S_source=0.05, S_visual=0.00, S_text=0.00, S_consist=0.00, S_action=0.00 |
| real risk evidence | 0.03 | keep_as_risk_evidence | low | S_source=0.05, S_visual=0.00, S_text=0.00, S_consist=0.10, S_action=0.00 |
| text injection | 0.40 | quarantine | high | S_source=0.40, S_visual=0.00, S_text=0.75, S_consist=0.85, S_action=0.00 |
| visual OCR injection | 0.49 | quarantine | high | S_source=0.05, S_visual=0.80, S_text=0.75, S_consist=0.85, S_action=0.00 |
| poisoned manual | 0.52 | quarantine | high | S_source=0.85, S_visual=0.15, S_text=0.75, S_consist=0.85, S_action=0.00 |
| parameter poisoning | 0.21 | need_human_review | medium | S_source=0.50, S_visual=0.00, S_text=0.00, S_consist=0.55, S_action=0.00 |
| image-text conflict | 0.34 | quarantine | high | S_source=0.05, S_visual=0.80, S_text=0.00, S_consist=0.85, S_action=0.00 |
| dangerous action query | 0.26 | refuse | high | S_source=0.05, S_visual=0.00, S_text=0.00, S_consist=0.55, S_action=0.70 |

## Project-Book Method Description

M-EPI treats multimodal evidence pollution as a measurable pre-answer risk. It does not simply block dangerous words. Instead, it distinguishes genuine manual risk warnings from malicious injection, forged evidence, parameter tampering, and image/text conflicts.
