#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pure Python SM2-like digest signing over the standard SM2 curve."""

from __future__ import annotations

import argparse
import secrets
from pathlib import Path
from typing import Optional, Tuple

from . import paths
from .gm_crypto import sm3_hash_text


P = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
A = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
B = 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93
N = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
GX = 0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7
GY = 0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0
Point = Optional[Tuple[int, int]]


def _inv(x: int, m: int) -> int:
    return pow(x % m, -1, m)


def _add(p1: Point, p2: Point) -> Point:
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        lam = ((3 * x1 * x1 + A) * _inv(2 * y1, P)) % P
    else:
        lam = ((y2 - y1) * _inv(x2 - x1, P)) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return x3, y3


def _mul(k: int, point: Point = (GX, GY)) -> Point:
    result: Point = None
    addend = point
    while k:
        if k & 1:
            result = _add(result, addend)
        addend = _add(addend, addend)
        k >>= 1
    return result


def _point_to_hex(point: Point) -> str:
    if point is None:
        raise ValueError("point at infinity cannot be encoded")
    return f"{point[0]:064x}{point[1]:064x}"


def _hex_to_point(value: str) -> Point:
    clean = value.strip().lower()
    if clean.startswith("04") and len(clean) == 130:
        clean = clean[2:]
    if len(clean) != 128:
        raise ValueError("SM2 public key must be 128 hex characters, or 130 with 04 prefix")
    return int(clean[:64], 16), int(clean[64:], 16)


def generate_keypair() -> tuple[str, str]:
    private = secrets.randbelow(N - 2) + 1
    public = _mul(private)
    return f"{private:064x}", _point_to_hex(public)


def sign_digest(digest_hex: str, private_key_hex: str) -> str:
    e = int(digest_hex, 16) % N
    d = int(private_key_hex, 16) % N
    if not 1 <= d < N:
        raise ValueError("invalid SM2 private key")
    while True:
        k = secrets.randbelow(N - 2) + 1
        point = _mul(k)
        if point is None:
            continue
        r = (e + point[0]) % N
        if r == 0 or r + k == N:
            continue
        s = (_inv(1 + d, N) * (k - r * d)) % N
        if s != 0:
            return f"{r:064x}{s:064x}"


def verify_digest(digest_hex: str, signature_hex: str, public_key_hex: str) -> bool:
    try:
        sig = signature_hex.strip().lower()
        if len(sig) != 128:
            return False
        r = int(sig[:64], 16)
        s = int(sig[64:], 16)
        if not (1 <= r < N and 1 <= s < N):
            return False
        public = _hex_to_point(public_key_hex)
        t = (r + s) % N
        if t == 0:
            return False
        point = _add(_mul(s), _mul(t, public))
        if point is None:
            return False
        e = int(digest_hex, 16) % N
        return ((e + point[0]) % N) == r
    except Exception:
        return False


def load_or_create_keys(key_dir: str | Path | None = None) -> tuple[str, str]:
    directory = Path(key_dir) if key_dir else paths.SAFE_DIR / "configs" / "gm_keys"
    directory.mkdir(parents=True, exist_ok=True)
    private_path = directory / "sm2_private_key.hex"
    public_path = directory / "sm2_public_key.hex"
    if private_path.exists() and public_path.exists():
        return private_path.read_text(encoding="utf-8").strip(), public_path.read_text(encoding="utf-8").strip()
    private, public = generate_keypair()
    private_path.write_text(private + "\n", encoding="utf-8")
    public_path.write_text(public + "\n", encoding="utf-8")
    return private, public


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-keys", action="store_true")
    args = parser.parse_args()
    private, public = load_or_create_keys()
    digest = sm3_hash_text("safeplc-sm2-self-test")
    signature = sign_digest(digest, private)
    ok = verify_digest(digest, signature, public)
    if args.init_keys:
        print(f"key_dir = {paths.SAFE_DIR / 'configs' / 'gm_keys'}")
    print(f"digest = {digest}")
    print(f"signature_len = {len(signature)}")
    print(f"public_key_len = {len(public)}")
    print(f"self_test = {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
