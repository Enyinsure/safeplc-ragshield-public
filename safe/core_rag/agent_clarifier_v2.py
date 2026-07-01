#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import re

from agent_planner_v1 import make_agent_plan, AgentPlan


@dataclass
class ClarificationDecision:
    original_question: str
    context: str
    enhanced_question: str
    needs_clarification: bool
    can_execute: bool
    clarification_reason: str
    clarifying_questions: List[str]
    suggested_context_examples: List[str]
    agent_v1_intent: str
    safety_level: str
    preferred_route: str
    missing_info: List[str]


def _contains_model_or_order_no(text: str) -> bool:
    patterns = [
        r"CPU\s*\d{4}[A-Z\-0-9 ]*",
        r"PS\s*\d+W[^，。；\n]*",
        r"SM\s*\d+[^，。；\n]*",
        r"AI\s*\d+[^，。；\n]*",
        r"AQ\s*\d+[^，。；\n]*",
        r"DI\s*\d+[^，。；\n]*",
        r"DQ\s*\d+[^，。；\n]*",
        r"6ES7[0-9A-Z\-]+",
    ]
    t = text.upper()
    return any(re.search(p, t, flags=re.IGNORECASE) for p in patterns)


def _rewrite_with_context(question: str, context: str, plan: AgentPlan) -> str:
    q = question.strip()
    c = context.strip()

    if not c:
        return q

    low = q.lower()

    # 针对最常见的缺型号参数问题，重写成更明确的问题，避免“某个模块”继续污染检索。
    if "电源电压" in low and ("允许范围" in low or "范围" in low or "多少" in low):
        return f"{c} 电源电压允许范围是多少"

    if "24" in low and ("端子" in low or "接线" in low or "怎么接" in low):
        return f"{c} 的 24 V DC 电源端子说明"

    if "超过" in low and "电源电压" in low:
        return f"{c} 电源电压超过允许范围还能不能运行"

    if "通信接口" in low or "接口" in low:
        return f"{c} {q}"

    return f"{c}：{q}"


def _clarifying_questions(plan: AgentPlan) -> List[str]:
    qs = []

    if any("型号" in x or "订货号" in x for x in plan.missing_info):
        qs.append("请补充具体 CPU / 模块型号或订货号，例如 CPU 1517-3 PN、PS 60W 24/48/60VDC HF 或 6ES7...。")

    if any("电源类型" in x for x in plan.missing_info):
        qs.append("请说明要查询的是系统电源、负载电源、CPU 本体电源，还是某个 PS/PM 电源模块。")

    if any("完整名称" in x for x in plan.missing_info):
        qs.append("请给出被询问对象的完整名称，避免把其它模块的参数误当作答案。")

    if not qs:
        qs.append("请补充足以唯一定位设备或章节的信息。")

    return qs


def _examples(plan: AgentPlan) -> List[str]:
    examples = []

    if plan.agent_intent in {"spec_or_table_query", "power_over_limit"}:
        examples.extend([
            "PS 60W 24/48/60VDC HF 电源电压允许范围是多少",
            "CPU 1517-3 PN 的电源电压允许范围是多少",
            "6ES7505-0RB00-0AB0 的电源电压允许范围是多少",
        ])

    if plan.agent_intent == "power_terminal_connection":
        examples.extend([
            "CPU 1517-3 PN 的 24 V DC 电源端子说明",
            "CPU 1515T-2 PN 的 1L+ 和 1M 是什么",
        ])

    if not examples:
        examples.extend([
            "CPU 1517-3 PN 的 PROFINET 接口 X1 X2",
            "PROFINET 环网如何连接 HMI 设备",
        ])

    return examples


def make_clarification_decision(question: str, context: Optional[str] = None) -> ClarificationDecision:
    context = (context or "").strip()
    plan = make_agent_plan(question)

    enhanced = _rewrite_with_context(question, context, plan)

    if plan.safety_level == "HIGH_RISK":
        return ClarificationDecision(
            original_question=question,
            context=context,
            enhanced_question=question,
            needs_clarification=False,
            can_execute=True,
            clarification_reason="高风险问题优先交由 Safety Guard v1 输出完整拒答，不要求用户补充操作细节。",
            clarifying_questions=[],
            suggested_context_examples=[],
            agent_v1_intent=plan.agent_intent,
            safety_level=plan.safety_level,
            preferred_route=plan.preferred_route,
            missing_info=plan.missing_info,
        )

    if context:
        return ClarificationDecision(
            original_question=question,
            context=context,
            enhanced_question=enhanced,
            needs_clarification=False,
            can_execute=True,
            clarification_reason="用户已补充上下文，Agent v2 将使用增强后的问题继续执行。",
            clarifying_questions=[],
            suggested_context_examples=[],
            agent_v1_intent=plan.agent_intent,
            safety_level=plan.safety_level,
            preferred_route=plan.preferred_route,
            missing_info=plan.missing_info,
        )

    if plan.missing_info and not plan.should_call_rag:
        return ClarificationDecision(
            original_question=question,
            context=context,
            enhanced_question=question,
            needs_clarification=True,
            can_execute=False,
            clarification_reason="当前问题缺少关键型号、订货号或对象信息；为避免误命中其它模块，Agent v2 将先追问而不是直接检索。",
            clarifying_questions=_clarifying_questions(plan),
            suggested_context_examples=_examples(plan),
            agent_v1_intent=plan.agent_intent,
            safety_level=plan.safety_level,
            preferred_route=plan.preferred_route,
            missing_info=plan.missing_info,
        )

    return ClarificationDecision(
        original_question=question,
        context=context,
        enhanced_question=question,
        needs_clarification=False,
        can_execute=True,
        clarification_reason="当前问题具备直接检索和回答的基本条件。",
        clarifying_questions=[],
        suggested_context_examples=[],
        agent_v1_intent=plan.agent_intent,
        safety_level=plan.safety_level,
        preferred_route=plan.preferred_route,
        missing_info=plan.missing_info,
    )


def format_clarification_block(decision: ClarificationDecision) -> str:
    missing = "；".join(decision.missing_info) if decision.missing_info else "无"
    questions = "\n".join([f"- {x}" for x in decision.clarifying_questions]) if decision.clarifying_questions else "- 无"
    examples = "\n".join([f"- {x}" for x in decision.suggested_context_examples]) if decision.suggested_context_examples else "- 无"
    execute = "是" if decision.can_execute else "否"
    clarify = "是" if decision.needs_clarification else "否"

    return f"""【Agent v2 澄清判断】
【原始问题】{decision.original_question}
【补充上下文】{decision.context if decision.context else "无"}
【增强后问题】{decision.enhanced_question}
【Agent v1 问题类型】{decision.agent_v1_intent}
【安全等级】{decision.safety_level}
【建议检索策略】{decision.preferred_route}
【缺失信息】{missing}
【是否需要澄清】{clarify}
【是否继续执行】{execute}
【判断理由】{decision.clarification_reason}

【建议追问】
{questions}

【可参考问法】
{examples}
"""


def to_dict(decision: ClarificationDecision) -> Dict:
    return asdict(decision)
