# Next-version Improvement Plan

## 1. 总目标

下一版目标是在不牺牲正常问题可用性的前提下，将 trusted online adversarial benchmark 从 74.8% 推进到 88%+。

必须保持：

- benign_pass_rate: keep 1.0
- poison_block_rate: keep 1.0
- canary_leak_count: keep 0
- poison_citation_count: keep 0
- audit_coverage: keep 1.0

## 2. 弱攻击族目标

- sensitive_disclosure: 0% -> 80%+
- improper_output_handling: 0% -> 80%+
- unbounded_consumption: 0% -> 90%+
- excessive_agency: 48.57% -> 85%+
- system_prompt_leakage: 51.43% -> 90%+
- direct_prompt_injection: 68% -> 90%+

总指标：

- total pass_rate: 74.8% -> 88%+

## 3. 实现路线

第一步：固化 benchmark 解释材料

- 使用 `benchmark/analyze_online_benchmark_results.py` 生成 online benchmark comparison report。
- 在报告中明确普通 RAG vs 审查型 Trusted RAG 的对比口径。
- 固定展示 pass_rate、benign_pass_rate、poison_block_rate、canary、poison citation 和 audit coverage。

第二步：补齐输入侧和输出侧 guard

- input intent guard 覆盖 direct prompt injection 和 system prompt leakage。
- sensitive output guard 覆盖 canary、token、key、prompt、配置文件泄露。
- output handling guard 覆盖危险 payload、伪造审计、破坏性 shell 命令。
- resource policy guard 覆盖无界资源消耗和 DoS 风险。
- agency policy guard 覆盖工业现场危险代理行为。

第三步：接入 trusted 链路和审计

- query guard 在 RAG 前执行，拒绝类请求不进入检索。
- answer guard 在回答后执行，防止模型输出危险内容。
- audit payload 记录 guard flags、guard decision、risk level 和 guard_results。

第四步：小回归先稳定，再跑下一轮 500 benchmark

- 先运行 `python -m safe.secguard.composite_security_guard --self-test`。
- 再运行 security guard regression，要求 accuracy >= 0.90 且 benign false positive = 0。
- 小回归稳定后，再由服务器环境运行下一轮 500 条 benchmark。

## 4. 展示口径

不要宣传 100% 防御。推荐口径：

- 当前 trusted 已经把 pass_rate 从 10.0% 提升到 74.8%，并保持 benign_pass_rate = 1.0。
- 最强证据是 canary 泄露归零、poison citation 归零、poison_block_rate 达到 1.0、audit_coverage 达到 1.0。
- 当前短板集中在输入侧意图识别和危险输出/资源/代理行为，下一版通过 composite guard 定向提升。
