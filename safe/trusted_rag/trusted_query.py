#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline trusted-answer pipeline for SafePLC RAG."""

from __future__ import annotations

import os
import json
import math
import re
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

for _thread_env in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ.setdefault(_thread_env, "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from . import paths
from .audit_logger import AuditLogger
from .consistency_checker import check_answer_supported
from .evidence_schema import EvidenceRecord, RetrievalTrace, TrustedAnswer
from .hash_chain import sha256_text
from .indirect_prompt_guard import scan_evidence_records
from .local_env import load_local_env, resolve_safe_path
from .poison_scanner import SEVERITY_ORDER, scan_query
from .risk_policy import decide


MAIN_COLLECTION = "s7_1500_manual"
FIGURE_COLLECTION = "s7_figures_v1"
DOMAIN_TERMS = [
    "S7-1500",
    "ET 200MP",
    "SIMATIC",
    "PROFINET",
    "PROFIBUS",
    "CPU",
    "HMI",
    "电源",
    "电压",
    "接线",
    "端子",
    "故障",
    "报警",
    "诊断",
    "安全",
    "订货号",
    "型号",
    "接口",
    "环网",
    "设备数量",
]
MODEL_RE = re.compile(r"(CPU\s*\d{4}[A-Z]*(?:[\-/][A-Z0-9]+)*(?:\s+[A-Z]{2,3})?|6ES[0-9A-Z\-_]+)", re.I)
GENERIC_TOKENS = {"plc", "cpu", "module", "manual", "safeplc"}


def find_embedding_model_path() -> Path | None:
    config = load_local_env()
    configured = os.environ.get("SAFE_EMBEDDING_MODEL_DIR") or config.get("SAFE_EMBEDDING_MODEL_DIR", "")
    if configured.strip():
        path = resolve_safe_path(configured)
        if path.exists():
            return path

    bases = [
        paths.resolve_path("models/BAAI"),
        Path.home() / ".cache" / "modelscope" / "BAAI",
    ]
    for base in bases:
        if not base.exists():
            continue
        if base.name.startswith("bge-small-zh-v1"):
            return base
        candidates = sorted(base.glob("bge-small-zh-v1*"))
        if candidates:
            return candidates[0]
    return None


@lru_cache(maxsize=1)
def _embedding_model() -> Any:
    model_path = find_embedding_model_path()
    if model_path is None:
        raise FileNotFoundError(
            "BGE embedding model not found. Set SAFE_EMBEDDING_MODEL_DIR to the local "
            "BAAI/bge-small-zh-v1.5 directory, or place it under ./models/BAAI/."
        )
    from sentence_transformers import SentenceTransformer

    try:
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        return SentenceTransformer(str(model_path), device=device)
    except Exception:
        return SentenceTransformer(str(model_path))


def _encode_query_embedding(query: str) -> List[float]:
    encoded = _embedding_model().encode([query], normalize_embeddings=True)
    return encoded[0].tolist()


def _has_specific_model_or_order(query: str) -> bool:
    return bool(MODEL_RE.search(query or ""))


def _query_needs_model_or_order(query: str) -> bool:
    q = query or ""
    sensitive_terms = [
        "接线",
        "端子",
        "电源电压",
        "允许范围",
        "故障灯",
        "LED",
        "输入",
        "输出",
        "订货号",
        "型号",
        "技术规范",
        "wiring",
        "terminal",
        "power supply",
        "fault led",
    ]
    return any(term.lower() in q.lower() for term in sensitive_terms) and not _has_specific_model_or_order(q)


def _add_missing_model_flag(query: str, risk: Dict[str, Any]) -> Dict[str, Any]:
    updated = {**risk, "risk_flags": list(risk.get("risk_flags", []))}
    if _query_needs_model_or_order(query):
        updated["risk_flags"] = sorted(set(updated["risk_flags"] + ["missing_model_or_order"]))
        updated["severity"] = max(
            updated.get("severity", "low"),
            "medium",
            key=lambda item: SEVERITY_ORDER.get(item, 0),
        )
        updated["reason"] = updated.get("reason", "") + " Missing specific model/order context."
    return updated


def _jsonl_records(path: Path, limit: int = 5000) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index >= limit:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError:
                continue


def _query_tokens(query: str) -> List[str]:
    q = query or ""
    tokens = set()
    for match in re.findall(r"[A-Za-z0-9][A-Za-z0-9+\-_/\.]*|[\u4e00-\u9fff]{2,}", q):
        token = match.strip().lower()
        if len(token) >= 2:
            tokens.add(token)
    for term in DOMAIN_TERMS:
        if term.lower() in q.lower():
            tokens.add(term.lower())
    return sorted(tokens)


def _normalize_compact(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower().replace("\u2011", "-")


def _query_identifiers(query: str) -> List[str]:
    return sorted({match.strip() for match in MODEL_RE.findall(query or "")})


def _unsupported_query_identifiers(query: str, evidence: Sequence[EvidenceRecord]) -> List[str]:
    evidence_text = _normalize_compact("\n".join(record.text for record in evidence))
    missing = []
    for identifier in _query_identifiers(query):
        if _normalize_compact(identifier) not in evidence_text:
            missing.append(identifier)
    return missing


def _score_record(query: str, text: str, metadata: Dict[str, Any]) -> float:
    combined = f"{text}\n{json.dumps(metadata, ensure_ascii=False)}".lower()
    tokens = _query_tokens(query)
    score = 0.0
    for token in tokens:
        if token in combined:
            if token in GENERIC_TOKENS:
                score += 0.5
            else:
                score += 2.0 + min(len(token), 12) / 12
    if (query or "").lower() in combined:
        score += 5.0
    return score


def _make_record(
    query_id: str,
    query: str,
    item: Dict[str, Any],
    source_type: str,
    collection: str,
    score: float,
) -> EvidenceRecord:
    metadata = dict(item.get("metadata") or {})
    text = str(item.get("text", ""))
    chunk_id = str(item.get("id") or metadata.get("chunk_id") or metadata.get("page_no") or "")
    page = metadata.get("page_no", item.get("page_no"))
    try:
        page_int = int(page) if page is not None else None
    except (TypeError, ValueError):
        page_int = None
    source_id = str(item.get("id") or metadata.get("source") or f"page_{page_int or 'unknown'}")
    return EvidenceRecord(
        query_id=query_id,
        query=query,
        source_id=source_id,
        source_type=source_type,
        collection=collection,
        page=page_int,
        chunk_id=chunk_id,
        text=text,
        score=float(score),
        risk_flags=[],
        hash=sha256_text(text),
        metadata=metadata,
    )


def _fallback_retrieve(query_id: str, query: str, top_k: int = 4) -> RetrievalTrace:
    start = time.time()
    candidates: List[Tuple[float, Dict[str, Any], str]] = []

    for item in _jsonl_records(paths.CHUNKS_JSONL):
        text = str(item.get("text", ""))
        score = _score_record(query, text, dict(item.get("metadata") or {}))
        if score >= 2.0:
            candidates.append((score, item, "sample_chunk"))

    if len(candidates) < top_k:
        for item in _jsonl_records(paths.PAGES_JSONL):
            text = str(item.get("text", ""))
            score = _score_record(query, text, item)
            if score >= 2.0:
                candidates.append((score * 0.85, item, "sample_page"))

    candidates.sort(key=lambda entry: entry[0], reverse=True)
    evidence = [
        _make_record(query_id, query, item, source_type, "sample_jsonl", min(score / 10.0, 1.0))
        for score, item, source_type in candidates[:top_k]
        if score >= 2.0
    ]
    status = "ok" if evidence else "no_evidence"
    warnings = []
    if not paths.CHUNKS_JSONL.exists():
        warnings.append(f"chunks JSONL missing: {paths.CHUNKS_JSONL}")
    if not paths.PAGES_JSONL.exists():
        warnings.append(f"pages JSONL missing: {paths.PAGES_JSONL}")
    return RetrievalTrace(
        query_id=query_id,
        query=query,
        collection="sample_jsonl",
        status=status,
        evidence=evidence,
        source="fallback_jsonl",
        warnings=warnings,
        latency_ms=(time.time() - start) * 1000,
    )


def _try_chroma_retrieve(query_id: str, query: str, top_k: int = 4) -> RetrievalTrace | None:
    if not paths.CHROMA_DIR.exists() or not paths.CHROMA_DIR.is_dir():
        return None
    start = time.time()
    try:
        import chromadb  # type: ignore
    except Exception:
        return None

    try:
        client = chromadb.PersistentClient(path=str(paths.CHROMA_DIR))
        collection = client.get_collection(MAIN_COLLECTION)
        query_embedding = _encode_query_embedding(query)
        result = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    except Exception:
        return None

    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    evidence: List[EvidenceRecord] = []
    for index, doc in enumerate(docs):
        metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
        distance = distances[index] if index < len(distances) else 1.0
        score = 1.0 / (1.0 + float(distance or 0.0))
        item = {"id": ids[index] if index < len(ids) else f"chroma_{index}", "text": doc, "metadata": metadata}
        evidence.append(_make_record(query_id, query, item, "chroma", MAIN_COLLECTION, score))
    return RetrievalTrace(
        query_id=query_id,
        query=query,
        collection=MAIN_COLLECTION,
        status="ok" if evidence else "no_evidence",
        evidence=evidence,
        source="chroma",
        warnings=[],
        latency_ms=(time.time() - start) * 1000,
    )


def retrieve_evidence(query_id: str, query: str) -> RetrievalTrace:
    chroma_trace = _try_chroma_retrieve(query_id, query)
    if chroma_trace is not None:
        return chroma_trace
    return _fallback_retrieve(query_id, query)


def _snippet(text: str, limit: int = 260) -> str:
    collapsed = re.sub(r"\s+", " ", text or "").strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def _draft_answer(query: str, evidence: Sequence[EvidenceRecord]) -> str:
    if not evidence:
        return "No local evidence was retrieved for this question."
    lines = ["基于本地检索到的 SafePLC/S7 手册证据，保守摘要如下："]
    for record in evidence[:3]:
        lines.append(f"- {_snippet(record.text)}")
    lines.append("以上仅作为手册证据摘要；涉及现场操作时，应由合格人员结合具体型号、订货号和现场图纸复核。")
    return "\n".join(lines)


def _apply_evidence_risk(evidence: List[EvidenceRecord], evidence_risk: Dict[str, Any]) -> None:
    by_source = {item.get("source_id"): item for item in evidence_risk.get("records", [])}
    for record in evidence:
        item = by_source.get(record.source_id)
        if item and item.get("risk_flags"):
            record.risk_flags = sorted(set(record.risk_flags + list(item["risk_flags"])))


def trusted_answer(query: str) -> TrustedAnswer:
    query_id = uuid.uuid4().hex
    clean_query = (query or "").strip()
    query_risk = _add_missing_model_flag(clean_query, scan_query(clean_query))
    retrieval = retrieve_evidence(query_id, clean_query)
    evidence = list(retrieval.evidence)
    unsupported_identifiers = _unsupported_query_identifiers(clean_query, evidence)
    if unsupported_identifiers:
        query_risk["risk_flags"] = sorted(
            set(list(query_risk.get("risk_flags", [])) + ["unsupported_query_identifier"])
        )
        query_risk["unsupported_query_identifiers"] = unsupported_identifiers
        query_risk["severity"] = max(
            query_risk.get("severity", "low"),
            "medium",
            key=lambda item: SEVERITY_ORDER.get(item, 0),
        )
    evidence_risk = scan_evidence_records(evidence)
    _apply_evidence_risk(evidence, evidence_risk)
    draft = _draft_answer(clean_query, evidence)
    consistency = check_answer_supported(draft, evidence)
    decision = decide(
        query_id=query_id,
        query_risk=query_risk,
        evidence_risk=evidence_risk,
        consistency_risk=consistency,
        retrieval_status=retrieval.status,
        draft_answer=draft,
        evidence_count=len(evidence),
    )

    audit_payload = {
        "query_id": query_id,
        "query": clean_query,
        "query_risk": query_risk,
        "retrieval": {
            "status": retrieval.status,
            "source": retrieval.source,
            "collection": retrieval.collection,
            "evidence_count": len(evidence),
            "warnings": retrieval.warnings,
            "latency_ms": retrieval.latency_ms,
        },
        "evidence_risk": evidence_risk,
        "consistency": consistency,
        "decision": decision.to_dict(),
        "evidence_hashes": [record.hash for record in evidence],
    }
    audit_record = AuditLogger().log_event("trusted_answer", audit_payload)
    return TrustedAnswer(
        query_id=query_id,
        query=clean_query,
        action=decision.action,
        answer=decision.answer,
        evidence=evidence,
        risk_flags=decision.risk_flags,
        audit_id=audit_record["audit_id"],
        audit_path=audit_record["audit_path"],
        retrieval_status=retrieval.status,
        decision=decision,
    )
