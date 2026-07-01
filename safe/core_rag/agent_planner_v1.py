#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, asdict
from typing import List, Dict
import re

from safety_guard_v1 import evaluate_safety


@dataclass
class AgentPlan:
    question: str
    safety_level: str
    agent_intent: str
    preferred_route: str
    missing_info: List[str]
    evidence_targets: List[str]
    reasoning_notes: List[str]
    should_call_rag: bool
    should_block_direct_answer: bool


MODEL_PATTERNS = [
    r"CPU\s*\d{4}[A-Z\-0-9 ]*",
    r"PS\s*\d+W[^，。；\n]*",
    r"SM\s*\d+[^，。；\n]*",
    r"AI\s*\d+[^，。；\n]*",
    r"AQ\s*\d+[^，。；\n]*",
    r"DI\s*\d+[^，。；\n]*",
    r"DQ\s*\d+[^，。；\n]*",
    r"6ES7[0-9A-Z\-]+",
]


FIGURE_TERMS = [
    "图", "图示", "图片", "硬件图", "接线图", "接线",
    "端子", "引脚", "针脚", "接口", "连接器", "插头",
    "拓扑", "环网", "PROFINET", "PROFIBUS", "RJ45",
    "FastConnect", "X1", "X2", "X3", "P1", "P2",
    "HMI", "IRT", "同步域"
]

TABLE_TERMS = [
    "多少", "范围", "允许范围", "额定值", "下限", "上限",
    "参数", "技术数据", "技术规范", "订货号", "型号",
    "尺寸", "宽度", "高度", "深度", "重量", "电流",
    "电压", "功耗", "最大", "最小", "支持", "数量",
    "规格", "表", "EMC"
]

POWER_TERMS = [
    "24V", "24 V", "DC", "电源", "电源电压", "负载电源",
    "系统电源", "1L+", "2L+", "1M", "2M", "L+"
]

NETWORK_TERMS = [
    "PROFINET", "PROFIBUS", "环网", "HMI", "RJ45",
    "FastConnect", "X1", "X2", "X3", "P1", "P2", "IRT"
]


def _contains_any(question: str, terms: List[str]) -> List[str]:
    q_low = question.lower()
    hits = []
    for t in terms:
        if t.lower() in q_low:
            hits.append(t)
    return hits


def _has_model_or_order_no(question: str) -> bool:
    q = question.upper()
    for pat in MODEL_PATTERNS:
        if re.search(pat, q, flags=re.IGNORECASE):
            return True
    return False


def _detect_intent(question: str, safety_level: str) -> str:
    q = question.lower()

    if safety_level == "HIGH_RISK":
        return "high_risk_operation"

    if ("1l+" in q or "2l+" in q or "l+" in q) and ("1m" in q or "2m" in q or re.search(r"(?<![a-z0-9])m(?![a-z0-9])", q)):
        return "terminal_meaning"

    if "电源电压" in q and ("超过" in q or "超出" in q):
        return "power_over_limit"

    if "profinet" in q and "环网" in q and ("多少" in q or "最多" in q or "数量" in q):
        return "network_ring_limit"

    if _contains_any(question, NETWORK_TERMS) and ("连接" in q or "接口" in q or "怎么" in q or "如何" in q):
        return "network_interface_connection"

    if _contains_any(question, POWER_TERMS) and ("怎么" in q or "如何" in q or "接" in q):
        return "power_terminal_connection"

    if _contains_any(question, TABLE_TERMS):
        return "spec_or_table_query"

    if _contains_any(question, FIGURE_TERMS):
        return "figure_or_interface_query"

    return "general_manual_query"


def _preferred_route(question: str, intent: str, safety_level: str) -> str:
    if safety_level == "HIGH_RISK":
        return "safety_block"

    if intent in [
        "terminal_meaning",
        "power_terminal_connection",
        "network_interface_connection",
        "network_ring_limit",
        "figure_or_interface_query",
    ]:
        return "figure_first"

    if intent in [
        "spec_or_table_query",
        "power_over_limit",
    ]:
        return "table_first"

    fig_hits = _contains_any(question, FIGURE_TERMS)
    table_hits = _contains_any(question, TABLE_TERMS)

    if fig_hits and table_hits:
        return "mixed"

    if fig_hits:
        return "figure_first"

    if table_hits:
        return "table_first"

    return "mixed"


def _missing_info(question: str, intent: str) -> List[str]:
    missing = []
    q = question.lower()

    # 这些问题已有明确安全处理或通用图文证据，不强制要求型号
    if intent in {
        "high_risk_operation",
        "terminal_meaning",
        "network_ring_limit",
    }:
        return []

    # EMC 可作为通用规范/技术要求先检索，不强制要求具体模块型号
    if "emc" in q or "电磁兼容" in q:
        return []

    model_needed_intents = {
        "power_terminal_connection",
        "power_over_limit",
        "spec_or_table_query",
    }

    vague_module_refs = ["该模块", "这个模块", "某个模块", "模块", "它"]

    if intent in model_needed_intents and not _has_model_or_order_no(question):
        missing.append("具体 CPU / 模块型号或订货号")

    if any(x in q for x in vague_module_refs) and not _has_model_or_order_no(question):
        missing.append("被询问对象的完整名称，例如 CPU 1517-3 PN 或 PS 60W 24/48/60VDC HF")

    if "电源电压" in q and not _has_model_or_order_no(question):
        missing.append("电源类型和对应模块，例如系统电源、负载电源或具体 PS/CPU 型号")

    return sorted(set(missing))


def _evidence_targets(question: str, intent: str, route: str) -> List[str]:
    targets = []

    if route in ["figure_first", "mixed"]:
        targets.append("图文证据：接口图、接线图、端子分配图、拓扑图")

    if route in ["table_first", "mixed"]:
        targets.append("表格证据：技术规范、技术数据、允许范围、额定值")

    if intent in ["terminal_meaning", "power_terminal_connection"]:
        targets.append("重点证据页：24 V DC 电源端子分配，1L+ / 2L+ / 1M / 2M")

    if intent in ["network_ring_limit", "network_interface_connection"]:
        targets.append("重点证据页：PROFINET 环网、HMI 连接、X1/X2/X3 接口说明")

    if intent == "high_risk_operation":
        targets.append("安全护栏：拒绝危险操作步骤，仅允许安全边界说明")

    return targets


def make_agent_plan(question: str) -> AgentPlan:
    safety = evaluate_safety(question)
    intent = _detect_intent(question, safety.level)
    route = _preferred_route(question, intent, safety.level)
    missing = _missing_info(question, intent)
    targets = _evidence_targets(question, intent, route)

    notes = []
    notes.append(f"Safety Guard v1 判定风险等级为 {safety.level}。")
    notes.append(f"Agent v1 将问题识别为 {intent}。")
    notes.append(f"建议检索策略为 {route}。")

    if missing:
        notes.append("问题存在缺失信息，但 Agent v1 会先基于现有信息给出可核查回答，并提示补充。")
    else:
        notes.append("问题具备直接检索和回答的基本条件。")

    # 对缺少关键型号/订货号的参数类问题，不调用 RAG，避免误命中某个随机模块并给出误导性参数。
    critical_missing_intents = {
        "spec_or_table_query",
        "power_over_limit",
        "power_terminal_connection",
    }

    should_call_rag = not safety.block_direct_answer
    if missing and intent in critical_missing_intents:
        should_call_rag = False

    return AgentPlan(
        question=question,
        safety_level=safety.level,
        agent_intent=intent,
        preferred_route=route,
        missing_info=missing,
        evidence_targets=targets,
        reasoning_notes=notes,
        should_call_rag=should_call_rag,
        should_block_direct_answer=safety.block_direct_answer,
    )


def format_agent_plan(plan: AgentPlan) -> str:
    missing = "；".join(plan.missing_info) if plan.missing_info else "无"
    targets = "\n".join([f"- {x}" for x in plan.evidence_targets]) if plan.evidence_targets else "- 无特殊证据目标"
    notes = "\n".join([f"- {x}" for x in plan.reasoning_notes])

    return f"""【Agent 主动推理环 v1】
【问题类型】{plan.agent_intent}
【安全等级】{plan.safety_level}
【建议检索策略】{plan.preferred_route}
【缺失信息提示】{missing}

【证据目标】
{targets}

【推理说明】
{notes}
"""


def to_dict(plan: AgentPlan) -> Dict:
    return asdict(plan)
