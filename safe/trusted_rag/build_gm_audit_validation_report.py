#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a GM audit validation report."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from . import paths
from .audit_tamper_matrix import run_matrix, write_matrix_report
from .export_evidence_bundle import export_bundle
from .gm_crypto import sm3_hash_text
from .gm_sm2 import load_or_create_keys, sign_digest, verify_digest
from .multimodal_gm_sm2_audit_logger import (
    append_gm_sm2_audit,
    latest_audit_path,
    public_key_fingerprint,
    verify_gm_sm2_audit,
)
from .verify_evidence_bundle import verify_bundle


def build_validation() -> Dict[str, Any]:
    sm3_digest = sm3_hash_text("abc")
    sm3_ok = sm3_digest == "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0"
    private, public = load_or_create_keys()
    digest = sm3_hash_text("gm-audit-validation")
    signature = sign_digest(digest, private)
    sm2_ok = verify_digest(digest, signature, public)
    append_gm_sm2_audit({"query": "gm audit validation", "action": "answer", "answer": "validation"})
    audit_result = verify_gm_sm2_audit(latest_audit_path())
    bundle_path = export_bundle()
    bundle_result = verify_bundle(bundle_path)
    matrix_summary = run_matrix()
    matrix_md, matrix_json = write_matrix_report(matrix_summary)
    return {
        "sm3_digest": sm3_digest,
        "sm3_self_test": sm3_ok,
        "sm2_self_test": sm2_ok,
        "public_key_fingerprint": public_key_fingerprint(public),
        "audit_hash_chain_ok": audit_result["hash_chain_ok"],
        "audit_sm2_signature_ok": audit_result["sm2_signature_ok"],
        "audit_public_key_fingerprint_ok": audit_result.get("public_key_fingerprint_ok", True),
        "bundle_path": str(bundle_path),
        "bundle_verify": bundle_result,
        "tamper_matrix": matrix_summary,
        "tamper_matrix_report": str(matrix_md),
        "tamper_matrix_summary": str(matrix_json),
        "limitations": [
            "This repository contains a competition prototype implementation of SM3/SM2-style trusted audit.",
            "Production deployments should use certified GM cryptographic modules or hardware security modules.",
        ],
    }


def write_report(summary: Dict[str, Any]) -> tuple[Path, Path]:
    paths.FINAL_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_md = paths.FINAL_REPORT_DIR / f"GM_AUDIT_VALIDATION_REPORT_{stamp}.md"
    out_json = paths.FINAL_REPORT_DIR / f"GM_AUDIT_VALIDATION_SUMMARY_{stamp}.json"
    lines = [
        "# GM Audit Validation Report",
        "",
        "## SM3 Standard Sample",
        "",
        f"- SM3('abc') = {summary['sm3_digest']}",
        f"- self_test = {summary['sm3_self_test']}",
        "",
        "## SM2 Signature Verification",
        "",
        f"- self_test = {summary['sm2_self_test']}",
        f"- public_key_fingerprint = {summary['public_key_fingerprint']}",
        "",
        "## Audit Hash Chain Verification",
        "",
        f"- hash_chain_ok = {summary['audit_hash_chain_ok']}",
        f"- sm2_signature_ok = {summary['audit_sm2_signature_ok']}",
        f"- public_key_fingerprint_ok = {summary['audit_public_key_fingerprint_ok']}",
        "",
        "## Evidence Bundle Export And Verify",
        "",
        f"- bundle_path = {summary['bundle_path']}",
        f"- bundle_hash_ok = {summary['bundle_verify']['bundle_hash_ok']}",
        f"- sm2_signature_ok = {summary['bundle_verify']['sm2_signature_ok']}",
        f"- public_key_fingerprint_ok = {summary['bundle_verify']['public_key_fingerprint_ok']}",
        f"- result = {summary['bundle_verify']['result']}",
        "",
        "## Tamper Matrix",
        "",
    ]
    lines.extend(f"- {key} = {value}" for key, value in summary["tamper_matrix"].items())
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in summary["limitations"])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_md, out_json


def main() -> int:
    summary = build_validation()
    out_md, out_json = write_report(summary)
    ok = (
        summary["sm3_self_test"]
        and summary["sm2_self_test"]
        and summary["audit_hash_chain_ok"]
        and summary["audit_sm2_signature_ok"]
        and summary["bundle_verify"]["result"] == "PASS"
        and summary["tamper_matrix"]["matrix_pass"]
    )
    print(f"GM_AUDIT_VALIDATION_PASS = {ok}")
    print(f"out_md = {out_md}")
    print(f"out_json = {out_json}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

