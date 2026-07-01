#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, asdict
import re
from typing import List, Dict


@dataclass
class SafetyAssessment:
    level: str
    reason: str
    matched_terms: List[str]
    needs_human_review: bool
    block_direct_answer: bool


HIGH_RISK_TERMS = [
    "带电", "不断电", "运行中接线", "热接线",
    "短接", "旁路", "绕过", "屏蔽", "解除保护", "禁用保护",
    "禁用安全", "安全回路", "强制输出", "强制置位", "强制运行",
    "让设备继续运行", "跳过故障", "取消联锁", "屏蔽报警"
]

MEDIUM_RISK_TERMS = [
    "接线", "端子", "引脚", "针脚", "24 v", "24v", "dc",
    "电源", "负载电源", "系统电源", "电源电压",
    "profinet 环网", "环网", "hmi", "x1", "x2", "x3",
    "p1", "p2", "rj45", "fastconnect", "接口", "连接器"
]

LOW_RISK_TERMS = [
    "多少", "范围", "允许范围", "额定值", "技术规范",
    "技术数据", "订货号", "型号", "尺寸", "重量",
    "功耗", "电流", "电压", "最大", "最小", "参数"
]

ACTION_TERMS = [
    "怎么", "如何", "步骤", "操作", "接", "改", "设置",
    "短接", "强制", "屏蔽", "绕过", "解除", "运行"
]


def _hits(question: str, terms: List[str]) -> List[str]:
    q = question.lower()
    return [t for t in terms if t.lower() in q]


def _terminal_hits(question: str) -> List[str]:
    q = question.lower()
    hits = []

    patterns = [
        (r"(?<![a-z0-9])(?:1l\+|2l\+|l\+)(?![a-z0-9])", "L+"),
        (r"(?<![a-z0-9])(?:1m|2m|m)(?![a-z0-9])", "M"),
    ]

    for pattern, name in patterns:
        if re.search(pattern, q):
            hits.append(name)

    return hits


def evaluate_safety(question: str) -> SafetyAssessment:
    q = question.strip()
    high_hits = _hits(q, HIGH_RISK_TERMS)
    medium_hits = sorted(set(_hits(q, MEDIUM_RISK_TERMS) + _terminal_hits(q)))
    low_hits = _hits(q, LOW_RISK_TERMS)
    action_hits = _hits(q, ACTION_TERMS)

    if high_hits and action_hits:
        return SafetyAssessment(
            level="HIGH_RISK",
            reason="问题涉及可能导致人身伤害、设备损坏或绕过保护机制的现场操作。",
            matched_terms=sorted(set(high_hits + action_hits)),
            needs_human_review=True,
            block_direct_answer=True,
        )

    if high_hits:
        return SafetyAssessment(
            level="HIGH_RISK",
            reason="问题命中高风险工业控制关键词，需要人工复核。",
            matched_terms=sorted(set(high_hits)),
            needs_human_review=True,
            block_direct_answer=True,
        )

    if medium_hits:
        return SafetyAssessment(
            level="MEDIUM_RISK",
            reason="问题涉及工业设备接线、电源、端子、接口或通信连接，回答仅可作为手册说明。",
            matched_terms=sorted(set(medium_hits)),
            needs_human_review=True,
            block_direct_answer=False,
        )

    if low_hits:
        return SafetyAssessment(
            level="LOW_RISK",
            reason="问题主要是型号、参数或技术规范查询。",
            matched_terms=sorted(set(low_hits)),
            needs_human_review=False,
            block_direct_answer=False,
        )

    return SafetyAssessment(
        level="SAFE_INFO",
        reason="普通手册说明类问题。",
        matched_terms=[],
        needs_human_review=False,
        block_direct_answer=False,
    )


def format_safety_block(assessment: SafetyAssessment) -> str:
    matched = "、".join(assessment.matched_terms) if assessment.matched_terms else "无"

    if assessment.level == "HIGH_RISK":
        tip = (
            "该问题涉及高风险现场操作。我不能提供可能导致人身伤害、设备损坏、"
            "绕过保护机制或违反现场安全规程的具体操作步骤。可以提供手册中的端子定义、"
            "额定参数、风险点和安全检查清单。实际操作必须由具备资质的人员在断电、"
            "挂牌上锁和现场审核后执行。"
        )
    elif assessment.level == "MEDIUM_RISK":
        tip = (
            "该问题涉及工业设备接线、电源、端子、接口或通信连接。以下回答仅基于手册内容说明，"
            "不替代现场电气设计、调试规程或安全审核。实际操作前应断电，并由具备资质的人员核对"
            "订货号、端子定义、额定电压、现场图纸和厂家手册。"
        )
    elif assessment.level == "LOW_RISK":
        tip = "该问题属于技术参数或型号查询。回答以手册证据为准，涉及现场应用时仍需核对具体设备型号和订货号。"
    else:
        tip = "该问题属于普通说明类查询。"

    review = "是" if assessment.needs_human_review else "否"

    return (
        f"【工业安全护栏】已启用\n"
        f"【安全等级】{assessment.level}\n"
        f"【命中关键词】{matched}\n"
        f"【是否需要人工复核】{review}\n"
        f"【安全提示】{tip}\n"
    )


def to_dict(assessment: SafetyAssessment) -> Dict:
    return asdict(assessment)
