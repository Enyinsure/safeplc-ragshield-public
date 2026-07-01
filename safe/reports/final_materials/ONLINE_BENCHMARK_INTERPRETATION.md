# Online Benchmark Interpretation

## 1. 为什么这是普通 RAG vs Trusted RAG

本轮 500 条 online adversarial benchmark 不是“有 RAG vs 没有 RAG”的对比，而是“普通 RAG vs 审查型 Trusted RAG”的对比。两边使用相同样本数、相同 Chroma/BGE 检索、相同 poison overlay 条件，并且都真正调用 RAG：

- rag_called_count = 500
- chroma_case_count = 500
- fallback_case_count = 0

因此，差异主要来自 Trusted RAG 额外引入的 trusted review chain、evidence inspection、ingestion gate、risk policy 和 audit，而不是来自是否检索。

## 2. 为什么 benign_pass_rate 保持 1.0 很重要

工业安全系统不能只追求“拦得狠”。如果安全层大量误伤正常 PLC 维护、诊断、接线、告警解释问题，系统就很难被工程人员接受。本轮 trusted 结果中 benign_pass_rate = 1.0，说明安全层在提升攻击拦截能力的同时，没有破坏正常问题通过率。

这对于比赛展示很关键：它说明 SafePLC-RAGShield 不是简单关键词封禁，而是在尽量维持工程可用性的前提下增强安全审查。

## 3. 为什么 poison/canary/audit 是最强证据

本轮最有说服力的提升集中在三类指标：

- canary_leak_count: 97 -> 0
- poison_citation_count: 255 -> 0
- poison_block_rate: 0.3922 -> 1.0
- audit_coverage: 0.0 -> 1.0

这些指标直接对应可信 RAG 的核心风险：秘密泄露、恶意证据引用、污染证据进入回答、以及审计不可追溯。trusted 模式在这些指标上归零或满覆盖，说明安全链路不是只改善最终文本，而是覆盖了证据、策略和审计闭环。

## 4. 为什么不能只看 attack_block_rate

attack_block_rate 只能说明攻击是否被拦住，但不能解释为什么拦住，也不能证明系统是否保留了正常可用性。一个系统可以通过粗暴拒答拿到较高 attack_block_rate，却牺牲 benign_pass_rate。

本项目应同时展示：

- pass_rate: 0.100 -> 0.748
- benign_pass_rate: 1.0 -> 1.0
- poison_block_rate: 0.3922 -> 1.0
- canary_leak_count: 97 -> 0
- poison_citation_count: 255 -> 0
- audit_coverage: 0.0 -> 1.0

这组指标更能说明 Trusted RAG 的价值：正常问题不被误杀，污染证据被阻断，敏感泄露被压住，每次决策可审计。

## 5. 当前短板和下一版路线

trusted 当前总 pass_rate = 0.748，仍不能宣传为 100% 防御。剩余失败主要集中在输入侧意图识别、敏感披露、危险输出处理、无界资源消耗和过度代理行为：

- sensitive_disclosure: 0.0
- improper_output_handling: 0.0
- unbounded_consumption: 0.0
- excessive_agency: 0.4857
- system_prompt_leakage: 0.5143
- direct_prompt_injection: 0.68

下一版目标是在保持 benign_pass_rate = 1.0、poison_block_rate = 1.0、canary_leak_count = 0、poison_citation_count = 0、audit_coverage = 1.0 的前提下，将 total pass_rate 从 74.8% 推到 88%+。

固定结论口径：

Under identical Chroma/BGE retrieval, poison overlay, sample count, and no-fallback settings, the Trusted RAG review chain improves the online adversarial benchmark pass rate from 10.0% to 74.8% while keeping benign pass rate at 100%. It reduces canary leakage from 97 to 0, poisoned-evidence citation from 255 to 0, and increases audit coverage from 0 to 1.0. Remaining failures mainly concentrate on input-side intent recognition, sensitive disclosure, unsafe output handling, unbounded consumption, and excessive agency.
