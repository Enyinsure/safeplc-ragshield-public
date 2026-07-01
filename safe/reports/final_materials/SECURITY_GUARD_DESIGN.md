# Security Guard Design

## 1. Guard 目标

本轮新增 security guard 的目标不是重做 benchmark，也不是替代原有 M-EPI visual guard，而是补 trusted 模式在 6 个弱攻击族上的输入侧和输出侧安全审查能力：

- direct_prompt_injection
- system_prompt_leakage
- sensitive_disclosure
- improper_output_handling
- unbounded_consumption
- excessive_agency

## 2. input intent guard

入口文件：`safe/secguard/input_intent_guard.py`

职责：

- 识别忽略旧指令、角色劫持、jailbreak、DAN、bypass safety 等直接提示注入。
- 识别要求泄露 system prompt、developer message、hidden prompt、internal policy 的请求。
- 命中高危输入时返回 `decision = refuse`，并打上 `input_prompt_injection` 或 `system_prompt_leakage`。

## 3. sensitive output guard

入口文件：`safe/secguard/sensitive_output_guard.py`

职责：

- 识别 canary、token、api key、password、private key、SM2 private key、system prompt、local_paths.env、内部配置等敏感对象。
- 区分“解释密码保护原理”这类知识性问题和“输出具体密钥/token/配置文件内容”这类泄露请求。
- 对高危请求或高危回答返回 `decision = refuse`，并使用安全拒绝模板。

## 4. output handling guard

入口文件：`safe/secguard/output_handling_guard.py`

职责：

- 拦截可直接执行或可直接滥用的破坏性输出请求。
- 覆盖 `<script>`、`javascript:`、SQL injection payload、伪造审计日志、`rm -rf`、`mkfs`、`dd if=`、`chmod 777`、`curl | sh`、`sudo`、删除日志、清空审计、覆盖配置、禁用安全策略等模式。
- 拒绝危险输出，同时建议安全检查清单、只读诊断步骤或恢复前确认项。

## 5. resource policy guard

入口文件：`safe/secguard/resource_policy_guard.py`

职责：

- 识别无限循环、fork bomb、run until success、generate millions、create huge files、scan entire disk、scan all network、DoS/DDoS、打满 CPU/GPU、耗尽内存、写满磁盘等无界资源消耗请求。
- 返回 `decision = refuse`，并建议有上限、小规模、只读、限速的测试方案。

## 6. agency policy guard

入口文件：`safe/secguard/agency_policy_guard.py`

职责：

- 限制系统只提供建议、证据和安全检查清单，不直接代理危险工业动作。
- 拦截写入 PLC 参数、强制输出、强制运行、远程启动、禁用报警、禁用联锁、绕过急停、绕过保护、短接安全回路、自动下发程序等请求。
- 对缺少型号、订货号或现场上下文的接线、端子、电源、模块类问题返回 `clarify`。

## 7. composite decision priority

统一入口：`safe/secguard/composite_security_guard.py`

统一函数：

- `inspect_query_security(query, context=None)`
- `inspect_answer_security(query, answer, context=None)`

决策优先级：

- decision: `refuse > clarify > allow`
- risk_level: `high > medium > low > none`

聚合结果包含：

- decision
- risk_level
- flags
- reasons
- guard_results
- safe_answer

## 8. audit integration

`safe/trusted_rag/trusted_multimodal_query.py` 已将 composite guard 接入 trusted 链路：

- RAG 前先执行 `inspect_query_security`。
- `refuse` 时不进入 RAG，直接写 GM audit。
- `clarify` 时不进入 RAG，返回澄清请求并写 GM audit。
- 正常生成后执行 `inspect_answer_security`。
- 如果回答命中敏感披露或危险输出，则改写为拒绝或澄清。

审计 payload 记录：

- query_guard_flags
- answer_guard_flags
- security_guard_decision
- security_guard_risk_level
- guard_results
- security_guard_flags

## 9. regression test

轻量回归集：`safe/tests/security_guard_regression_cases.jsonl`

评测脚本：

```bash
python -m safe.secguard.eval_security_guard_regression \
  --cases safe/tests/security_guard_regression_cases.jsonl \
  --out_json safe/reports/security_guard_regression_summary.json
```

目标：

- accuracy >= 0.90
- benign false positive = 0
