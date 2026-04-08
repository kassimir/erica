"""Thin wrapper around local MemPalace (ChromaDB palace + optional package APIs)."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

COLLECTION_NAME = "mempalace_drawers"
DEFAULT_WING = "wing_erica"
DEFAULT_ROOM = "agent"


def _try_search_memories(
    query: str,
    palace_path: str,
    *,
    wing: str | None = None,
    room: str | None = None,
    n_results: int = 5,
) -> dict[str, Any]:
    try:
        from mempalace.searcher import search_memories
    except ImportError:
        return {"error": "mempalace package not installed", "results": []}
    return search_memories(query, palace_path, wing=wing, room=room, n_results=n_results)


def _chromadb_collection(palace_path: str, *, create: bool = False):
    try:
        import chromadb
    except ImportError:
        log.warning("chromadb not installed; MemPalace writes disabled")
        return None
    try:
        client = chromadb.PersistentClient(path=palace_path)
        if create:
            return client.get_or_create_collection(COLLECTION_NAME)
        return client.get_collection(COLLECTION_NAME)
    except Exception as e:
        log.warning("MemPalace Chroma at %s unavailable: %s", palace_path, e)
        return None


class MempalaceClient:
    """In-process MemPalace operations aligned with the upstream palace layout."""

    def __init__(self, palace_path: Path | str | None, identity_path: Path | str | None = None) -> None:
        self._palace_path = str(Path(palace_path).expanduser()) if palace_path else ""
        self._identity_path = (
            Path(identity_path).expanduser()
            if identity_path
            else Path.home() / ".mempalace" / "identity.txt"
        )

    @property
    def palace_ready(self) -> bool:
        return bool(self._palace_path) and Path(self._palace_path).is_dir()

    def search(
        self,
        query: str,
        *,
        wing: str | None = None,
        room: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        if not self.palace_ready:
            return {"error": "no palace path", "results": []}
        return _try_search_memories(query, self._palace_path, wing=wing, room=room, n_results=limit)

    def add_drawer(
        self,
        wing: str,
        room: str,
        content: str,
        *,
        source_file: str = "",
        added_by: str = "erica_agent",
        extra_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.palace_ready:
            return {"success": False, "error": "no palace path"}
        col = _chromadb_collection(self._palace_path, create=True)
        if not col:
            return {"success": False, "error": "chromadb unavailable"}

        drawer_id = (
            f"drawer_{wing}_{room}_"
            f"{hashlib.md5((content[:100] + datetime.now().isoformat()).encode()).hexdigest()[:16]}"
        )
        meta: dict[str, Any] = {
            "wing": wing,
            "room": room,
            "source_file": source_file,
            "chunk_index": 0,
            "added_by": added_by,
            "filed_at": datetime.now().isoformat(),
        }
        if extra_meta:
            meta.update({k: str(v) for k, v in extra_meta.items()})

        try:
            col.add(ids=[drawer_id], documents=[content], metadatas=[meta])
            log.info("MemPalace drawer %s → %s/%s", drawer_id, wing, room)
            return {"success": True, "drawer_id": drawer_id, "wing": wing, "room": room}
        except Exception as e:
            log.exception("add_drawer failed")
            return {"success": False, "error": str(e)}

    def diary_write(self, agent_name: str, entry: str, topic: str = "general") -> dict[str, Any]:
        """Mirror mempalace MCP tool_diary_write: one wing per agent, room diary."""
        if not self.palace_ready:
            return {"success": False, "error": "no palace path"}
        col = _chromadb_collection(self._palace_path, create=True)
        if not col:
            return {"success": False, "error": "chromadb unavailable"}

        wing = f"wing_{agent_name.lower().replace(' ', '_')}"
        now = datetime.now()
        entry_id = (
            f"diary_{wing}_{now.strftime('%Y%m%d_%H%M%S')}_"
            f"{hashlib.md5(entry[:50].encode()).hexdigest()[:8]}"
        )
        try:
            col.add(
                ids=[entry_id],
                documents=[entry],
                metadatas=[
                    {
                        "wing": wing,
                        "room": "diary",
                        "hall": "hall_diary",
                        "topic": topic,
                        "type": "diary_entry",
                        "agent": agent_name,
                        "filed_at": now.isoformat(),
                        "date": now.strftime("%Y-%m-%d"),
                    }
                ],
            )
            return {"success": True, "entry_id": entry_id}
        except Exception as e:
            log.exception("diary_write failed")
            return {"success": False, "error": str(e)}

    def read_identity_file(self) -> str:
        p = self._identity_path
        if not p.is_file():
            return ""
        try:
            return p.read_text(encoding="utf-8").strip()
        except OSError:
            return ""
