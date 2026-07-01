#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the full final SafePLC-RAGShield validation chain."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from safe.multimodal_guard.build_visual_db_coverage_report import build_coverage
from safe.multimodal_guard.verify_visual_evidence_provenance import verify_provenance
from safe.secguard import demo_security_showcase
from safe.trusted_rag import paths
from safe.trusted_rag.audit_tamper_matrix import run_matrix, write_matrix_report
from safe.trusted_rag.build_final_security_report import build_report
from safe.trusted_rag.eval_multimodal_poison_guard import evaluate, load_cases, write_csv
from safe.trusted_rag.export_evidence_bundle import export_bundle
from safe.trusted_rag.gm_crypto import sm3_hash_text
from safe.trusted_rag.gm_sm2 import load_or_create_keys, sign_digest, verify_digest
from safe.trusted_rag.multimodal_gm_sm2_audit_logger import append_gm_sm2_audit, latest_audit_path, verify_gm_sm2_audit
from safe.trusted_rag.multimodal_poison_guard import inspect_visual_evidence
from safe.trusted_rag.tamper_test_gm_sm2_audit import _tamper
from safe.trusted_rag.trusted_multimodal_query import trusted_multimodal_answer
from safe.trusted_rag.verify_evidence_bundle import verify_bundle


def _eval(case_name: str, out_name: str) -> Dict[str, Any]:
    case_path = paths.SAFE_DIR / "tests" / case_name
    result = evaluate(load_cases(case_path))
    paths.EVAL_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = paths.EVAL_DIR / f"{out_name}.csv"
    out_summary = paths.EVAL_DIR / f"{out_name}_summary.json"
    write_csv(result["rows"], out_csv)
    summary = {key: value for key, value in result.items() if key != "rows"}
    summary["out_csv"] = str(out_csv)
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def run_validation() -> Dict[str, Any]:
    coverage = build_coverage()
    provenance = verify_provenance("pdf_page_01965")
    smoke = _eval("mepi_visual_guard_cases.jsonl", "mepi_visual_guard_eval")
    mepi_100 = _eval("mepi_visual_guard_cases_100.jsonl", "mepi_visual_guard_eval_100")
    pdf_01965 = inspect_visual_evidence(
        {
            "evidence_id": "pdf_page_01965",
            "text": "Warning wiring error diagnostic diagram shows short-circuit fault.",
            "visual_type": "wiring_error_diagram",
        }
    )
    demo = trusted_multimodal_answer("terminal wiring figure power module", visual_n=2)
    sm3_ok = sm3_hash_text("abc") == "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0"
    private, public = load_or_create_keys()
    digest = sm3_hash_text("full-final-validation")
    sm2_ok = verify_digest(digest, sign_digest(digest, private), public)
    append_gm_sm2_audit({"query": "full final validation", "action": "answer", "answer": "validation"})
    audit = verify_gm_sm2_audit(latest_audit_path())
    tampered = _tamper(latest_audit_path())
    tamper = verify_gm_sm2_audit(tampered)
    matrix = run_matrix()
    write_matrix_report(matrix)
    bundle_path = export_bundle()
    bundle = verify_bundle(bundle_path)
    showcase_ok = demo_security_showcase.main() == 0
    final_report = build_report()

    critical_pass = (
        smoke["total"] == 8
        and smoke["correct"] == 8
        and mepi_100["total"] == 100
        and mepi_100["correct"] == 100
        and pdf_01965["decision"] == "keep_as_risk_evidence"
        and sm3_ok
        and sm2_ok
        and audit["hash_chain_ok"]
        and audit["sm2_signature_ok"]
        and (not tamper["ok"])
        and matrix["matrix_pass"]
        and bundle["result"] == "PASS"
        and showcase_ok
    )
    return {
        "visual_db_coverage": coverage,
        "visual_provenance_pdf_page_01965": provenance,
        "mepi_smoke": smoke,
        "mepi_100": mepi_100,
        "pdf_page_01965_decision": pdf_01965["decision"],
        "trusted_multimodal_demo": {
            "action": demo["action"],
            "risk_flags": demo["risk_flags"],
            "hash_algorithm": demo["hash_algorithm"],
            "signature_algorithm": demo["signature_algorithm"],
        },
        "sm3_self_test": sm3_ok,
        "sm2_self_test": sm2_ok,
        "audit_logger_verify": audit,
        "tamper_detected": not tamper["ok"],
        "tamper_matrix": matrix,
        "evidence_bundle_verify": bundle,
        "security_showcase": showcase_ok,
        "final_report": str(final_report),
        "warnings": coverage["warnings"] + provenance["warnings"],
        "FINAL_VALIDATION_PASS": critical_pass,
    }


def write_validation_outputs(summary: Dict[str, Any]) -> tuple[Path, Path]:
    paths.FINAL_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_txt = paths.FINAL_REPORT_DIR / f"FULL_FINAL_VALIDATION_{stamp}.txt"
    out_json = paths.FINAL_REPORT_DIR / f"FULL_FINAL_VALIDATION_SUMMARY_{stamp}.json"
    lines = [
        "SafePLC-RAGShield Full Final Validation",
        f"M-EPI smoke: total={summary['mepi_smoke']['total']} correct={summary['mepi_smoke']['correct']} accuracy={summary['mepi_smoke']['accuracy']}",
        f"M-EPI-100: total={summary['mepi_100']['total']} correct={summary['mepi_100']['correct']} accuracy={summary['mepi_100']['accuracy']}",
        f"pdf_page_01965 -> {summary['pdf_page_01965_decision']}",
        f"SM3 self_test = {summary['sm3_self_test']}",
        f"SM2 self_test = {summary['sm2_self_test']}",
        f"hash_chain_ok = {summary['audit_logger_verify']['hash_chain_ok']}",
        f"sm2_signature_ok = {summary['audit_logger_verify']['sm2_signature_ok']}",
        f"tamper_detected = {summary['tamper_detected']}",
        f"matrix_pass = {summary['tamper_matrix']['matrix_pass']}",
        f"bundle_verify = {summary['evidence_bundle_verify']['result']}",
        f"SHOWCASE_PASS = {summary['security_showcase']}",
        f"warnings = {summary['warnings'] or 'none'}",
        f"final_report = {summary['final_report']}",
        f"FINAL_VALIDATION_PASS = {summary['FINAL_VALIDATION_PASS']}",
    ]
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_txt, out_json


def main() -> int:
    summary = run_validation()
    out_txt, out_json = write_validation_outputs(summary)
    print(f"FINAL_VALIDATION_PASS = {summary['FINAL_VALIDATION_PASS']}")
    print(f"out_txt = {out_txt}")
    print(f"out_json = {out_json}")
    return 0 if summary["FINAL_VALIDATION_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

