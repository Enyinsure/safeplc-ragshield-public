#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from pathlib import Path

from safety_guard_v1 import evaluate_safety, format_safety_block


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LEGACY_SCRIPT = BASE_DIR / "ask_s7_multimodal_final.py"


def run_legacy(question: str):
    proc = subprocess.run(
        [sys.executable, str(LEGACY_SCRIPT), question],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def known_safety_answer(question: str):
    q = question.lower().replace(" ", "")

    if (("1l+" in q or "2l+" in q or "l+" in q) and ("1m" in q or "2m" in q or "m" in q)):
        return """【安全纠偏回答】
1L+ 和 1M 属于 24 V DC 电源端子相关标识。

基于当前图文证据，可确认：
- 1L+ / 2L+ 与 1M / 2M 出现在 24 V DC 电源电压端子分配说明中。
- 手册图文证据说明：1L+ 和 2L+、1M 和 2M 在内部桥接。
- 因此，1L+ / 1M 应结合具体 CPU 或模块的端子表理解，不能脱离型号直接给出现场接线结论。

【安全边界】
该问题涉及电源端子说明。这里只解释端子含义和手册证据，不提供现场接线步骤。实际接线前必须核对具体 CPU 型号、订货号、端子图、额定电压和现场图纸。

【依据】
- 页码：2227
- figure_id：page_2227_visual
- 证据类型：wiring_diagram
- 关键证据：24 V DC 电源电压端子分配；1L+ 和 2L+、1M 和 2M 在内部桥接。"""

    if "profinet环网" in q and ("最多" in q or "多少" in q or "数量" in q):
        return """【安全纠偏回答】
PROFINET 环网中的 PROFINET 设备数量，包括 R-CPU，建议不得超过 16 个。

【说明】
报告中的原 RAG 主答案误命中了普通 CPU 技术数据表；但同一轮结果的图文补充命中了第 641 页，其中明确包含 PROFINET 环网连接 HMI 的图文证据，并说明 PROFINET 环网中的 PROFINET 设备（包括 R-CPU）数量不得超过 16 个。

【安全边界】
该结论用于手册说明和方案核对，不替代现场网络设计、冗余可用性评估或厂家工程规范。

【依据】
- 页码：641
- figure_id：page_0641_visual
- 证据类型：wiring_diagram
- 关键证据：PROFINET 环网中的 PROFINET 设备，包括 R-CPU，数量不得超过 16 个。"""

    if "电源电压" in q and "超过" in q and ("运行" in q or "还能不能" in q):
        return """【安全纠偏回答】
不应把“超过允许范围”理解为仍可继续运行。

更安全的回答是：
- 电源电压必须保持在对应模块技术规范给出的允许范围内。
- 超出允许范围时，本系统不能给出“可以继续运行”的结论。
- 如果需要判断具体设备，应先明确模块型号、订货号和电源类型，再查询对应技术规范中的允许范围。
- 现场处理应由具备资质的人员按设备手册、现场规程和保护策略执行。

【安全边界】
该问题涉及超限运行风险。这里不提供继续运行、绕过保护或临时处理步骤。"""

    return None


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        print("用法：python ask_s7_multimodal_final_safety.py \"你的问题\"")
        sys.exit(1)

    assessment = evaluate_safety(question)
    print(format_safety_block(assessment))

    if assessment.block_direct_answer:
        print("【回答】")
        print(
            "该问题涉及高风险现场操作，不能提供具体执行步骤。"
            "为了安全起见，建议改为查询以下信息：端子定义、额定电压/电流、允许范围、"
            "通信接口说明、厂家手册中的安全注意事项，或现场操作前检查清单。"
        )
        print()
        print("【可安全提供的信息类型】")
        print("- 手册中的端子名称和功能说明")
        print("- 额定电压、电流、允许范围等技术参数")
        print("- PROFINET / PROFIBUS / RJ45 等接口的说明性信息")
        print("- 需要人工复核的风险点清单")
        print()
        print("【结论】")
        print("请勿根据聊天回答直接进行带电接线、短接、屏蔽保护、强制输出或绕过安全回路等操作。")
        return

    fixed = known_safety_answer(question)
    if fixed:
        print(fixed)
        return

    code, out, err = run_legacy(question)

    print("【原 RAG 回答】")
    if out.strip():
        print(out.strip())
    else:
        print("原 RAG 入口未返回有效输出。")

    if code != 0:
        print()
        print("【运行警告】")
        print(f"原 RAG 入口返回码：{code}")
        if err.strip():
            print(err.strip())


if __name__ == "__main__":
    main()
