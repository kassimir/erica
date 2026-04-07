"""Deterministic text embeddings (hashing trick) — no ML dependencies."""

from __future__ import annotations

import hashlib
import math

EMBED_DIM = 256


def embed_text(text: str) -> list[float]:
    """Map text to a fixed-size L2-normalized vector for cosine similarity."""
    t = (text or "").lower().strip()
    vec = [0.0] * EMBED_DIM
    if not t:
        return vec

    for i in range(len(t) - 1):
        h = hashlib.sha256(t[i : i + 2].encode()).digest()
        idx = int.from_bytes(h[:2], "big") % EMBED_DIM
        vec[idx] += 1.0

    for c in t:
        h = hashlib.sha256(bytes([ord(c)])).digest()
        idx = int.from_bytes(h[:2], "big") % EMBED_DIM
        vec[idx] += 0.35

    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 0:
        return vec
    return [x / norm for x in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))
