#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run audit-chain verification and tamper-detection demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from safe.trusted_rag.audit_report import (
    build_hash_chain,
    demo_events,
    export_audit_report,
    load_events_jsonl,
    tamper_one_event,
    verify_hash_chain,
    write_events_jsonl,
)


def write_doc(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Audit Chain Specification

Industrial safety RAG needs an audit chain because every answer may depend on retrieved evidence, risk decisions, and safety gates. A tamper-evident log lets reviewers reproduce what happened.

Each event records `event_id`, `timestamp`, `query`, `decision`, `risk_level`, `evidence_hashes`, `prev_hash`, `current_hash`, `signature_algorithm`, `signature_ok`, `key_id`, and `metadata`.

`prev_hash` links each event to the previous event. `current_hash` is computed from the stable event payload. If any earlier event is changed, verification fails at that event or the following link.

The `signature_algorithm` field is compatible with future SM2 integration. In this lightweight repository it is explicitly marked `SM2-compatible-demo`; it is not a real national-cryptography signature.

Limitations: without a real key-management module, the signature layer is a demo-compatible placeholder. The hash-chain tamper-detection logic is still useful for offline demonstrations and project reports.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-log")
    parser.add_argument("--output-dir", default="safe/reports")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    events = load_events_jsonl(args.input_log) if args.input_log else demo_events()
    original_verify = verify_hash_chain(events)
    tampered = tamper_one_event(events)
    tampered_verify = verify_hash_chain(tampered)

    write_events_jsonl(events, output_dir / "audit_chain_demo_original.jsonl")
    write_events_jsonl(tampered, output_dir / "audit_chain_demo_tampered.jsonl")
    verify_payload = {"original": original_verify, "tampered": tampered_verify}
    (output_dir / "audit_chain_verify_result.json").write_text(
        json.dumps(verify_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    export_audit_report(events, original_verify, output_dir / "audit_chain_report.md")
    with (output_dir / "audit_chain_report.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Tamper Demo\n\n")
        handle.write(f"- Original verification OK: {original_verify['ok']}\n")
        handle.write(f"- Tampered verification OK: {tampered_verify['ok']}\n")
        handle.write(f"- Tamper detected: {tampered_verify['tamper_detected']}\n")
        handle.write(f"- Tamper errors: {'; '.join(tampered_verify['errors'])}\n")
    write_doc(ROOT / "safe" / "docs" / "AUDIT_CHAIN_SPEC.md")
    print(f"wrote {output_dir / 'audit_chain_report.md'}")
    return 0 if original_verify["ok"] and tampered_verify["tamper_detected"] else 1


if __name__ == "__main__":
    sys.exit(main())
