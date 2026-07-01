#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pure Python SM3 helpers."""

from __future__ import annotations

import json
from typing import Any, Iterable, List


IV = [
    0x7380166F,
    0x4914B2B9,
    0x172442D7,
    0xDA8A0600,
    0xA96F30BC,
    0x163138AA,
    0xE38DEE4D,
    0xB0FB0E4E,
]


def _rotl(x: int, n: int) -> int:
    n %= 32
    return ((x << n) & 0xFFFFFFFF) | ((x & 0xFFFFFFFF) >> (32 - n))


def _p0(x: int) -> int:
    return x ^ _rotl(x, 9) ^ _rotl(x, 17)


def _p1(x: int) -> int:
    return x ^ _rotl(x, 15) ^ _rotl(x, 23)


def _ff(x: int, y: int, z: int, j: int) -> int:
    return x ^ y ^ z if j <= 15 else (x & y) | (x & z) | (y & z)


def _gg(x: int, y: int, z: int, j: int) -> int:
    return x ^ y ^ z if j <= 15 else (x & y) | (~x & z)


def _padding(data: bytes) -> bytes:
    bit_len = len(data) * 8
    padded = data + b"\x80"
    while len(padded) % 64 != 56:
        padded += b"\x00"
    return padded + bit_len.to_bytes(8, "big")


def _words(block: bytes) -> tuple[List[int], List[int]]:
    w = [int.from_bytes(block[i : i + 4], "big") for i in range(0, 64, 4)]
    for j in range(16, 68):
        w.append(_p1(w[j - 16] ^ w[j - 9] ^ _rotl(w[j - 3], 15)) ^ _rotl(w[j - 13], 7) ^ w[j - 6])
    w1 = [w[j] ^ w[j + 4] for j in range(64)]
    return w, w1


def _compress(v: List[int], block: bytes) -> List[int]:
    w, w1 = _words(block)
    a, b, c, d, e, f, g, h = v
    for j in range(64):
        tj = 0x79CC4519 if j <= 15 else 0x7A879D8A
        ss1 = _rotl((_rotl(a, 12) + e + _rotl(tj, j)) & 0xFFFFFFFF, 7)
        ss2 = ss1 ^ _rotl(a, 12)
        tt1 = (_ff(a, b, c, j) + d + ss2 + w1[j]) & 0xFFFFFFFF
        tt2 = (_gg(e, f, g, j) + h + ss1 + w[j]) & 0xFFFFFFFF
        d = c
        c = _rotl(b, 9)
        b = a
        a = tt1
        h = g
        g = _rotl(f, 19)
        f = e
        e = _p0(tt2)
    out = [a, b, c, d, e, f, g, h]
    return [(out[i] ^ v[i]) & 0xFFFFFFFF for i in range(8)]


def sm3_hash(data: bytes) -> str:
    v = IV[:]
    padded = _padding(data)
    for i in range(0, len(padded), 64):
        v = _compress(v, padded[i : i + 64])
    return "".join(f"{word:08x}" for word in v)


def sm3_hash_text(text: str) -> str:
    return sm3_hash(text.encode("utf-8"))


def canonical_json_hash(obj: Any) -> str:
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sm3_hash_text(data)


def main() -> int:
    digest = sm3_hash_text("abc")
    expected = "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0"
    print(f"SM3('abc') = {digest}")
    print(f"self_test = {digest == expected}")
    return 0 if digest == expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
