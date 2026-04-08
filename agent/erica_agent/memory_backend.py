"""Memory abstraction: MemPalace primary + SQLite read-through cache; optional HTTP backend later."""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from erica_agent.config import settings
from erica_agent.embeddings import embed_text
from erica_agent.erica_memory import get_erica_memory
from erica_agent.memory import long_term as sqlite_cache

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
    """Erica MemPalace facade + SQLite cache."""

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
        return get_erica_memory().store_utterance(
            text,
            metadata=metadata,
            tags=tags,
            source=source,
            label=label,
        )

    def search(self, query: str, *, limit: int = 5, wing: str | None = None) -> list[dict[str, Any]]:
        if not query.strip():
            return sqlite_cache.retrieve_relevant(None, limit=limit)

        lines = get_erica_memory().recall(query, wing=wing, room=None)
        out: list[dict[str, Any]] = []
        for i, line in enumerate(lines[:limit]):
            out.append(
                {
                    "label": "mempalace",
                    "payload": {"text": line},
                    "score": 1.0 - i * 0.01,
                }
            )
        if out:
            return out

        q_emb = embed_text(query)
        return sqlite_cache.retrieve_relevant(q_emb, limit=limit)

    def identity_core(self) -> str:
        return get_erica_memory().identity_l0()

    def diary(self, entry: str, *, wing: str | None = None) -> None:
        agent = (wing or "erica").replace("Mode", "").replace(" ", "_").lower() or "erica"
        r = get_erica_memory().log_diary(entry, agent_name=agent)
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
