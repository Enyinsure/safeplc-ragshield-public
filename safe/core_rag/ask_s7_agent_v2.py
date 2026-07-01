#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import sys
from pathlib import Path

from agent_clarifier_v2 import make_clarification_decision, format_clarification_block


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
AGENT_V1_SCRIPT = BASE_DIR / "ask_s7_agent_v1.py"


def run_agent_v1(question: str):
    proc = subprocess.run(
        [sys.executable, str(AGENT_V1_SCRIPT), question],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def main():
    parser = argparse.ArgumentParser(
        description="S7 多模态 RAG Agent v2：多轮澄清 / 自动追问 / Safety Guard 继承"
    )
    parser.add_argument("question", nargs="*", help="用户问题")
    parser.add_argument("--context", default="", help="用户补充上下文，例如型号、订货号、模块名称")
    parser.add_argument("--force", action="store_true", help="即使缺少信息也强制调用 Agent v1，不推荐")
    args = parser.parse_args()

    question = " ".join(args.question).strip()

    if not question:
        print("用法：python ask_s7_agent_v2.py \"你的问题\"")
        print("示例：python ask_s7_agent_v2.py \"某个模块的电源电压允许范围是多少\" --context \"PS 60W 24/48/60VDC HF\"")
        sys.exit(1)

    decision = make_clarification_decision(question, args.context)

    print(format_clarification_block(decision))

    if decision.needs_clarification and not args.force:
        print("【Agent v2 执行结果】")
        print("当前问题需要先补充关键信息。Agent v2 已停止自动检索，避免误命中其它模块并输出误导性参数。")
        print()
        print("你可以使用如下方式继续：")
        print(f'python {Path(__file__).name} "{question}" --context "PS 60W 24/48/60VDC HF"')
        return

    run_question = decision.enhanced_question

    print("【Agent v2 调用 Agent v1】")
    print(f"执行问题：{run_question}")
    print()

    code, out, err = run_agent_v1(run_question)

    print("【Agent v2 最终回答】")
    if out.strip():
        print(out.strip())
    else:
        print("Agent v1 未返回有效输出。")

    if code != 0:
        print()
        print("【Agent v2 运行警告】")
        print(f"Agent v1 返回码：{code}")
        if err.strip():
            print(err.strip())


if __name__ == "__main__":
    main()
