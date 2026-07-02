#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SM4 local sealing for SafePLC audit JSONL files."""

from __future__ import annotations

import argparse
import base64
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from . import paths
from .gm_crypto import sm3_hash
from .gm_sm4 import sm4_cbc_decrypt, sm4_cbc_encrypt, self_test as sm4_self_test


SEAL_VERSION = 1
SEAL_ALGORITHM = "SM4"
SEAL_MODE = "CBC"
SEAL_PADDING = "PKCS7"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _key_dir(key_dir: str | Path | None = None) -> Path:
    directory = Path(key_dir) if key_dir else paths.SAFE_DIR / "configs" / "gm_keys"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def load_or_create_sm4_key(key_dir: str | Path | None = None) -> bytes:
    path = _key_dir(key_dir) / "sm4_key.hex"
    if path.exists():
        key = bytes.fromhex(path.read_text(encoding="utf-8").strip())
        if len(key) != 16:
            raise ValueError(f"invalid SM4 key length in {path}")
        return key
    key = secrets.token_bytes(16)
    path.write_text(key.hex() + "\n", encoding="utf-8")
    return key


def default_sealed_path(audit_path: str | Path) -> Path:
    source = Path(audit_path)
    return source.with_name(source.name + ".sm4.json")


def _envelope_without_ciphertext(envelope: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in envelope.items() if key not in {"ciphertext_b64", "envelope_sm3"}}


def seal_audit_log(
    audit_path: str | Path | None = None,
    output_path: str | Path | None = None,
    key_dir: str | Path | None = None,
) -> Dict[str, Any]:
    source = Path(audit_path) if audit_path else paths.AUDIT_DIR
    if source.is_dir():
        candidates = sorted(source.glob("audit_multimodal_gm_sm2_*.jsonl"))
        if not candidates:
            raise FileNotFoundError(f"no GM SM2 audit JSONL found under {source}")
        source = candidates[-1]
    if not source.exists():
        raise FileNotFoundError(source)

    plaintext = source.read_bytes()
    key = load_or_create_sm4_key(key_dir)
    iv = secrets.token_bytes(16)
    ciphertext = sm4_cbc_encrypt(plaintext, key, iv)
    sealed_path = Path(output_path) if output_path else default_sealed_path(source)
    sealed_path.parent.mkdir(parents=True, exist_ok=True)

    envelope: Dict[str, Any] = {
        "version": SEAL_VERSION,
        "sealed_at": _utc_now(),
        "source_name": source.name,
        "source_path": str(source),
        "algorithm": SEAL_ALGORITHM,
        "mode": SEAL_MODE,
        "padding": SEAL_PADDING,
        "iv_hex": iv.hex(),
        "key_fingerprint_sm3": sm3_hash(key),
        "plaintext_size": len(plaintext),
        "plaintext_sm3": sm3_hash(plaintext),
        "ciphertext_size": len(ciphertext),
        "ciphertext_sm3": sm3_hash(ciphertext),
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
    }
    envelope["envelope_sm3"] = sm3_hash(
        json.dumps(_envelope_without_ciphertext(envelope), ensure_ascii=False, sort_keys=True).encode("utf-8")
    )
    sealed_path.write_text(json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "source_path": str(source),
        "sealed_path": str(sealed_path),
        "algorithm": f"{SEAL_ALGORITHM}-{SEAL_MODE}-{SEAL_PADDING}",
        "plaintext_size": len(plaintext),
        "ciphertext_size": len(ciphertext),
        "plaintext_sm3": envelope["plaintext_sm3"],
        "ciphertext_sm3": envelope["ciphertext_sm3"],
        "key_fingerprint_sm3": envelope["key_fingerprint_sm3"],
    }


def open_sealed_audit(sealed_path: str | Path, key_dir: str | Path | None = None) -> bytes:
    path = Path(sealed_path)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    if envelope.get("algorithm") != SEAL_ALGORITHM or envelope.get("mode") != SEAL_MODE:
        raise ValueError("unsupported audit seal envelope")
    expected_envelope_sm3 = sm3_hash(
        json.dumps(_envelope_without_ciphertext(envelope), ensure_ascii=False, sort_keys=True).encode("utf-8")
    )
    if envelope.get("envelope_sm3") != expected_envelope_sm3:
        raise ValueError("sealed audit envelope SM3 mismatch")
    key = load_or_create_sm4_key(key_dir)
    if sm3_hash(key) != envelope.get("key_fingerprint_sm3"):
        raise ValueError("SM4 key fingerprint does not match sealed audit envelope")
    ciphertext = base64.b64decode(envelope["ciphertext_b64"])
    if sm3_hash(ciphertext) != envelope.get("ciphertext_sm3"):
        raise ValueError("sealed audit ciphertext SM3 mismatch")
    plaintext = sm4_cbc_decrypt(ciphertext, key, bytes.fromhex(envelope["iv_hex"]))
    if len(plaintext) != int(envelope.get("plaintext_size", -1)):
        raise ValueError("sealed audit plaintext size mismatch")
    if sm3_hash(plaintext) != envelope.get("plaintext_sm3"):
        raise ValueError("sealed audit plaintext SM3 mismatch")
    return plaintext


def verify_sealed_audit(
    sealed_path: str | Path,
    key_dir: str | Path | None = None,
    expected_plaintext_path: str | Path | None = None,
) -> Dict[str, Any]:
    path = Path(sealed_path)
    errors = []
    plaintext = b""
    try:
        plaintext = open_sealed_audit(path, key_dir=key_dir)
    except Exception as exc:
        errors.append(str(exc))

    expected_match = None
    if expected_plaintext_path and plaintext:
        expected = Path(expected_plaintext_path).read_bytes()
        expected_match = sm3_hash(expected) == sm3_hash(plaintext)
        if not expected_match:
            errors.append("decrypted plaintext does not match expected audit file")

    return {
        "ok": not errors,
        "sealed_path": str(path),
        "plaintext_size": len(plaintext),
        "expected_plaintext_match": expected_match,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seal or verify SafePLC audit logs with SM4-CBC.")
    parser.add_argument("--seal", nargs="?", const="", help="Audit JSONL path to seal. Omit value to seal latest audit.")
    parser.add_argument("--verify", help="Sealed *.sm4.json envelope to verify and decrypt in memory.")
    parser.add_argument("--decrypt", help="Sealed *.sm4.json envelope to decrypt to --output.")
    parser.add_argument("--output", help="Output path for --seal or --decrypt.")
    parser.add_argument("--expected", help="Expected plaintext JSONL path for --verify.")
    parser.add_argument("--key-dir", help="Directory containing local sm4_key.hex.")
    parser.add_argument("--self-test", action="store_true", help="Run SM4 block/CBC self-test.")
    args = parser.parse_args()

    if args.self_test:
        ok = sm4_self_test()
        print(json.dumps({"sm4_self_test": ok}, ensure_ascii=False, indent=2))
        return 0 if ok else 1

    if args.verify:
        result = verify_sealed_audit(args.verify, key_dir=args.key_dir, expected_plaintext_path=args.expected)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1

    if args.decrypt:
        if not args.output:
            raise SystemExit("--decrypt requires --output")
        plaintext = open_sealed_audit(args.decrypt, key_dir=args.key_dir)
        Path(args.output).write_bytes(plaintext)
        print(json.dumps({"ok": True, "output": args.output, "plaintext_size": len(plaintext)}, ensure_ascii=False, indent=2))
        return 0

    if args.seal is not None:
        audit_path = None if args.seal == "" else args.seal
        result = seal_audit_log(audit_path=audit_path, output_path=args.output, key_dir=args.key_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
