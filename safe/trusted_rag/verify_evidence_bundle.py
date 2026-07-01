#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independently verify an exported evidence bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from . import paths
from .export_evidence_bundle import export_bundle
from .gm_crypto import canonical_json_hash, sm3_hash_text
from .gm_sm2 import verify_digest


def _latest_bundle() -> Path:
    directory = paths.SAFE_DIR / "reports" / "audit_bundles"
    existing = sorted(directory.glob("bundle_*.json"))
    if existing:
        return existing[-1]
    return export_bundle()


def verify_bundle(path: str | Path | None = None) -> Dict[str, Any]:
    bundle_path = Path(path) if path else _latest_bundle()
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    record_hash = str(bundle.get("record_hash", ""))
    record_body = bundle.get("record_body")
    bundle_hash_ok = bool(record_body) and canonical_json_hash(record_body) == record_hash
    public_key = str(bundle.get("sm2_public_key", ""))
    sm2_signature_ok = verify_digest(record_hash, str(bundle.get("sm2_signature", "")), public_key)
    public_key_fingerprint_ok = sm3_hash_text(public_key) == str(bundle.get("public_key_fingerprint", ""))
    result = bundle_hash_ok and sm2_signature_ok and public_key_fingerprint_ok and bool(record_hash)
    return {
        "bundle_path": str(bundle_path),
        "bundle_hash_ok": bundle_hash_ok,
        "sm2_signature_ok": sm2_signature_ok,
        "public_key_fingerprint_ok": public_key_fingerprint_ok,
        "record_hash_present": bool(record_hash),
        "result": "PASS" if result else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--latest", action="store_true")
    group.add_argument("--bundle")
    args = parser.parse_args()
    result = verify_bundle(args.bundle)
    for key in ["bundle_hash_ok", "sm2_signature_ok", "public_key_fingerprint_ok", "record_hash_present", "result"]:
        print(f"{key} = {result[key]}")
    print(f"bundle_path = {result['bundle_path']}")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

