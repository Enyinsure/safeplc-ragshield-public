#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from pathlib import Path

from agent_planner_v1 import make_agent_plan, format_agent_plan


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
SAFETY_SCRIPT = BASE_DIR / "ask_s7_multimodal_final_safety.py"


def run_safety_rag(question: str):
    proc = subprocess.run(
        [sys.executable, str(SAFETY_SCRIPT), question],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        print("用法：python ask_s7_agent_v1.py \"你的问题\"")
        sys.exit(1)

    plan = make_agent_plan(question)

    print(format_agent_plan(plan))

    if plan.missing_info:
        print("【Agent 缺失信息处理】")
        print("当前问题缺少关键型号或对象信息。Agent v1 不会编造缺失条件，也不会把其它模块的参数当作当前问题答案。")
        print("建议补充：")
        for item in plan.missing_info:
            print(f"- {item}")
        print()

    if not plan.should_call_rag:
        print("【Agent 执行结果】")
        if plan.should_block_direct_answer:
            code, out, err = run_safety_rag(question)
            if out.strip():
                print(out.strip())
            else:
                print("该问题已由 Safety Guard v1 判定为高风险操作，应拒绝危险步骤。")
            if code != 0:
                print()
                print("【Agent 运行警告】")
                print(f"Safety Guard v1 返回码：{code}")
                if err.strip():
                    print(err.strip())
        else:
            print("当前问题缺少关键型号 / 订货号 / 对象信息，Agent v1 已停止自动检索，避免误命中其它模块并输出误导性参数。")
            print("请补充具体对象后再查询，例如：")
            print("- PS 60W 24/48/60VDC HF 电源电压允许范围是多少")
            print("- CPU 1517-3 PN 的电源电压允许范围是多少")
        return

    code, out, err = run_safety_rag(question)

    print("【Agent 执行结果】")
    if out.strip():
        print(out.strip())
    else:
        print("Safety Guard v1 入口未返回有效输出。")

    if code != 0:
        print()
        print("【Agent 运行警告】")
        print(f"Safety Guard v1 返回码：{code}")
        if err.strip():
            print(err.strip())


if __name__ == "__main__":
    main()
