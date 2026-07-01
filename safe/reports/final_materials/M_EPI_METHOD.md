# M-EPI Method

## 1. Definition

M-EPI means Multimodal Evidence Pollution Inspection. It is a rule-based inspection layer for visual/OCR/table evidence before that evidence can influence a trusted industrial RAG answer.

## 2. Inputs And Outputs

Input is one Evidence Card or a list of Evidence Cards. Output is a decision, risk level, flags, and reasons for each card plus aggregate kept/quarantined/risk evidence lists.

## 3. Evidence Decisions

- `keep`: clean evidence can be used normally.
- `keep_as_risk_evidence`: real industrial risk evidence is preserved and audited.
- `quarantine`: malicious, forged, or prompt-injection evidence is isolated.

## 4. Three Detection Layers

- Layer 1: Instruction Injection Detection detects OCR text such as “ignore previous instructions” or “reveal system prompt”.
- Layer 2: Authority Forgery Detection detects fake safety rules, fake vendor updates, and universal wiring conclusions.
- Layer 3: Risk Evidence Preservation detects real warnings, faults, alarms, wrong wiring, diagnostics, and maintenance events.

## 5. Decision Priority

`prompt injection > poisoned evidence > real risk evidence > clean`

If forged evidence contains warning terms, it is still quarantined. If a real manual warning contains risk words, it is retained as risk evidence.

## 6. Why M-EPI Is Not Dangerous-Word Filtering

M-EPI 的关键不是过滤危险词，而是区分“真实风险证据”和“恶意污染证据”。工业手册中的错误接线、报警、故障、诊断等内容本身是必要安全证据，不能被简单删除。

## 7. `pdf_page_01965` Case

`pdf_page_01965` represents real wrong-wiring or diagnostic visual evidence. It should be classified as `keep_as_risk_evidence`, not `quarantine`, because the system must preserve real risk evidence for safe clarification and audit.

## 8. Limitations And Future Work

The current implementation is deliberately offline and deterministic. Future work can add certified OCR confidence, richer visual type models, and adversarial hard sets. This version intentionally does not add M-EPI-HARD-50.

