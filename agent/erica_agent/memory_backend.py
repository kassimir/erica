"""Memory abstraction: MemPalace primary + SQLite read-through cache; optional HTTP backend later."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from erica_agent.config import settings
from erica_agent.embeddings import embed_text
from erica_agent.memory import long_term as sqlite_cache
from erica_agent.mempalace_client import DEFAULT_WING, MempalaceClient

log = logging.getLogger(__name__)


@runtime_checkable
class MemoryBackend(Protocol):
    def write(
        self,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        source: str = "erica",
        label: str = "entry",
    ) -> str:
        """Persist long-term text; returns opaque id (cache row or drawer id)."""

    def search(self, query: str, *, limit: int = 5, wing: str | None = None) -> list[dict[str, Any]]:
        """Semantic or hybrid retrieval; dicts match SQLite row shape for context formatting."""

    def identity_core(self) -> str:
        """Short L0-style identity block for prompts."""

    def diary(self, entry: str, *, wing: str | None = None) -> None:
        """Append a diary entry (agent name / mode maps to MemPalace wing)."""


class MemPalaceLocalBackend:
    """MemPalace via in-process client; SQLite stores embeddings for fast local fallback."""

    def __init__(self) -> None:
        path = settings.mempalace_palace_path
        if path is None:
            path = Path.home() / ".mempalace" / "palace"
        self._client = MempalaceClient(
            palace_path=path,
            identity_path=settings.mempalace_identity_path,
        )

    def write(
        self,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        source: str = "erica",
        label: str = "entry",
        **_: Any,
    ) -> str:
        meta = dict(metadata or {})
        if tags:
            meta["tags"] = tags
        wing = DEFAULT_WING
        room = label or "agent"
        if tags:
            if tags[0].startswith("wing_"):
                wing = tags[0]
                room = tags[1] if len(tags) > 1 else "agent"
            else:
                room = tags[0]

        r = self._client.add_drawer(
            wing,
            room,
            text,
            extra_meta=meta,
            added_by=source,
        )
        if not r.get("success"):
            log.debug("MemPalace write skipped: %s", r.get("error"))

        payload = {"text": text[:2000], **meta, "mempalace": r}
        try:
            return sqlite_cache.write_metadata_and_index_text(source, label, payload, text)
        except Exception:
            log.exception("SQLite cache write failed")
            return str(r.get("drawer_id") or "")

    def search(self, query: str, *, limit: int = 5, wing: str | None = None) -> list[dict[str, Any]]:
        if not query.strip():
            return sqlite_cache.retrieve_relevant(None, limit=limit)

        raw = self._client.search(query, wing=wing, room=None, limit=limit)
        hits = raw.get("results") if isinstance(raw, dict) else None
        out: list[dict[str, Any]] = []
        if isinstance(hits, list):
            for h in hits:
                if not isinstance(h, dict):
                    continue
                text = h.get("text") or ""
                sim = h.get("similarity")
                out.append(
                    {
                        "label": "mempalace",
                        "payload": {"text": text, "wing": h.get("wing"), "room": h.get("room")},
                        "score": float(sim) if isinstance(sim, (int, float)) else None,
                    }
                )
        if out:
            return out[:limit]

        q_emb = embed_text(query)
        return sqlite_cache.retrieve_relevant(q_emb, limit=limit)

    def identity_core(self) -> str:
        core = self._client.read_identity_file()
        if core:
            return core[:4000]
        return ""

    def diary(self, entry: str, *, wing: str | None = None) -> None:
        agent = wing or "erica"
        r = self._client.diary_write(agent, entry, topic="session")
        if not r.get("success"):
            log.debug("MemPalace diary skipped: %s", r.get("error"))


class MemPalaceHttpBackend:
    """Placeholder: until HTTP mapping exists, SQLite cache only (no remote MemPalace)."""

    def write(
        self,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        source: str = "erica",
        label: str = "entry",
        **_: Any,
    ) -> str:
        meta = dict(metadata or {})
        if tags:
            meta["tags"] = tags
        log.warning(
            "MemPalaceHttpBackend: HTTP bridge not implemented; writing SQLite cache only"
        )
        return sqlite_cache.write_metadata_and_index_text(source, label, meta, text)

    def search(self, query: str, *, limit: int = 5, wing: str | None = None) -> list[dict[str, Any]]:
        if not query.strip():
            return sqlite_cache.retrieve_relevant(None, limit=limit)
        return sqlite_cache.retrieve_relevant(embed_text(query), limit=limit)

    def identity_core(self) -> str:
        return ""

    def diary(self, entry: str, *, wing: str | None = None) -> None:
        log.debug("MemPalaceHttpBackend: diary skipped until HTTP bridge (wing=%s)", wing)


_backend: MemoryBackend | None = None


def get_memory_backend() -> MemoryBackend:
    global _backend
    if _backend is None:
        mode = (settings.memory_backend or "local").strip().lower()
        if mode == "http":
            _backend = MemPalaceHttpBackend()
        else:
            _backend = MemPalaceLocalBackend()
    return _backend


def reset_memory_backend_for_tests() -> None:
    global _backend
    _backend = None
