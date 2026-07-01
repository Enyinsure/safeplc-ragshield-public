#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dataclass schemas used by the trusted RAG security layer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _from_dict(cls, data: Dict[str, Any]):
    names = {field.name for field in fields(cls)}
    return cls(**{name: data[name] for name in names if name in data})


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    return value


EVIDENCE_CARD_FIELDS = [
    "evidence_id",
    "source_file",
    "page_id",
    "modality",
    "content",
    "ocr_text",
    "table_text",
    "bbox",
    "linked_text_chunks",
    "risk_tags",
    "source_hash",
    "is_real_risk_evidence",
    "is_poisoned",
    "metadata",
]

VALID_MODALITIES = {"text", "table", "image", "page", "ocr"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _string_list(value: Any) -> List[str]:
    return [str(item) for item in _as_list(value) if item is not None]


def _metadata(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


@dataclass
class EvidenceCard:
    evidence_id: str
    source_file: str
    page_id: str | int
    modality: str
    content: str = ""
    ocr_text: str = ""
    table_text: str = ""
    bbox: Optional[List[Any]] = None
    linked_text_chunks: List[str] = field(default_factory=list)
    risk_tags: List[str] = field(default_factory=list)
    source_hash: str = ""
    is_real_risk_evidence: bool = False
    is_poisoned: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceCard":
        return cls(**normalize_evidence_card(data))


def _stable_card_payload(card: Dict[str, Any]) -> Dict[str, Any]:
    return {field_name: card.get(field_name) for field_name in EVIDENCE_CARD_FIELDS if field_name != "source_hash"}


def compute_card_hash(card: Dict[str, Any]) -> str:
    normalized = dict(card)
    if set(EVIDENCE_CARD_FIELDS).difference(normalized):
        normalized = normalize_evidence_card(normalized)
    payload = json.dumps(
        _stable_card_payload(normalized),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_evidence_card(raw: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(raw or {})
    content = _string_or_empty(data.get("content"))
    ocr_text = _string_or_empty(data.get("ocr_text"))
    table_text = _string_or_empty(data.get("table_text"))
    linked = _string_list(data.get("linked_text_chunks"))
    source_file = _string_or_empty(data.get("source_file") or data.get("source") or "unknown")
    page_id = data.get("page_id", data.get("page", data.get("page_no", "")))
    evidence_id = _string_or_empty(
        data.get("evidence_id")
        or data.get("id")
        or data.get("chunk_id")
        or hashlib.sha256(f"{source_file}|{page_id}|{content[:80]}".encode("utf-8")).hexdigest()[:16]
    )
    modality = _string_or_empty(data.get("modality") or data.get("source_type") or "text").lower()
    if modality not in VALID_MODALITIES:
        modality = "text"

    bbox = data.get("bbox")
    if bbox is not None and not isinstance(bbox, list):
        bbox = [bbox]

    card = {
        "evidence_id": evidence_id,
        "source_file": source_file,
        "page_id": page_id,
        "modality": modality,
        "content": content,
        "ocr_text": ocr_text,
        "table_text": table_text,
        "bbox": bbox,
        "linked_text_chunks": linked,
        "risk_tags": _string_list(data.get("risk_tags")),
        "source_hash": _string_or_empty(data.get("source_hash")),
        "is_real_risk_evidence": _bool_value(data.get("is_real_risk_evidence")),
        "is_poisoned": _bool_value(data.get("is_poisoned")),
        "metadata": _metadata(data.get("metadata")),
    }
    if not card["source_hash"]:
        card["source_hash"] = compute_card_hash(card)
    return card


def validate_evidence_card(card: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field_name in EVIDENCE_CARD_FIELDS:
        if field_name not in card:
            errors.append(f"missing field: {field_name}")
    if card.get("modality") not in VALID_MODALITIES:
        errors.append(f"invalid modality: {card.get('modality')!r}")
    if not str(card.get("evidence_id", "")).strip():
        errors.append("evidence_id must not be empty")
    if not str(card.get("source_file", "")).strip():
        errors.append("source_file must not be empty")
    if not any(str(card.get(name, "")).strip() for name in ("content", "ocr_text", "table_text")):
        errors.append("one of content, ocr_text, or table_text must be present")
    if card.get("bbox") is not None and not isinstance(card.get("bbox"), list):
        errors.append("bbox must be a list or null")
    for list_field in ("linked_text_chunks", "risk_tags"):
        if not isinstance(card.get(list_field), list):
            errors.append(f"{list_field} must be a list")
    if not isinstance(card.get("metadata"), dict):
        errors.append("metadata must be a dict")
    for bool_field in ("is_real_risk_evidence", "is_poisoned"):
        if not isinstance(card.get(bool_field), bool):
            errors.append(f"{bool_field} must be a bool")
    return errors


@dataclass
class EvidenceRecord:
    query_id: str
    query: str
    source_id: str
    source_type: str
    collection: str
    page: Optional[int]
    chunk_id: str
    text: str
    score: float = 0.0
    risk_flags: List[str] = field(default_factory=list)
    hash: str = ""
    created_at: str = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceRecord":
        obj = _from_dict(cls, data)
        obj.risk_flags = [str(item) for item in _as_list(obj.risk_flags)]
        return obj


@dataclass
class RetrievalTrace:
    query_id: str
    query: str
    collection: str
    status: str
    evidence: List[EvidenceRecord] = field(default_factory=list)
    source: str = "fallback"
    warnings: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return _to_plain(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalTrace":
        evidence = [
            item if isinstance(item, EvidenceRecord) else EvidenceRecord.from_dict(item)
            for item in data.get("evidence", [])
        ]
        obj = _from_dict(cls, {**data, "evidence": evidence})
        obj.warnings = [str(item) for item in _as_list(obj.warnings)]
        return obj


@dataclass
class RiskDecision:
    query_id: str
    action: str
    reason: str
    risk_flags: List[str] = field(default_factory=list)
    severity: str = "low"
    answer: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskDecision":
        obj = _from_dict(cls, data)
        obj.risk_flags = [str(item) for item in _as_list(obj.risk_flags)]
        return obj


@dataclass
class TrustedAnswer:
    query_id: str
    query: str
    action: str
    answer: str
    evidence: List[EvidenceRecord] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    audit_id: str = ""
    audit_path: str = ""
    retrieval_status: str = ""
    created_at: str = field(default_factory=utc_now)
    decision: Optional[RiskDecision] = None

    def to_dict(self) -> Dict[str, Any]:
        return _to_plain(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustedAnswer":
        evidence = [
            item if isinstance(item, EvidenceRecord) else EvidenceRecord.from_dict(item)
            for item in data.get("evidence", [])
        ]
        decision_data = data.get("decision")
        decision = None
        if isinstance(decision_data, RiskDecision):
            decision = decision_data
        elif isinstance(decision_data, dict):
            decision = RiskDecision.from_dict(decision_data)
        obj = _from_dict(cls, {**data, "evidence": evidence, "decision": decision})
        obj.risk_flags = [str(item) for item in _as_list(obj.risk_flags)]
        return obj
