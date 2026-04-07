"""Short-term (in-process) and long-term (SQLite) memory for the Erica agent."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any

from erica_agent.config import settings
from erica_agent.embeddings import cosine_similarity, embed_text
from erica_agent.models import EricaMode


class ShortTermMemory:
    """Recent commands, active tasks, and app hints (session-scoped)."""

    def __init__(self, max_commands: int = 50) -> None:
        self._lock = threading.Lock()
        self._commands: deque[dict[str, Any]] = deque(maxlen=max_commands)
        self._tasks: list[dict[str, Any]] = []
        self._open_apps: list[str] = []
        self._last_mode: EricaMode | None = None

    def add_command(self, text: str, meta: dict[str, Any] | None = None) -> None:
        with self._lock:
            self._commands.append(
                {
                    "text": text,
                    "ts": time.time(),
                    "meta": meta or {},
                }
            )

    def set_active_tasks(self, tasks: list[dict[str, Any]]) -> None:
        with self._lock:
            self._tasks = list(tasks)

    def set_open_apps(self, apps: list[str]) -> None:
        with self._lock:
            self._open_apps = list(apps)

    def set_last_mode(self, mode: EricaMode) -> None:
        with self._lock:
            self._last_mode = mode

    def summary(self) -> str:
        with self._lock:
            recent = list(self._commands)[-10:]
            lines = ["Recent commands:"]
            for c in recent:
                lines.append(f"- {c.get('text', '')}")
            lines.append("Active tasks:")
            for t in self._tasks:
                lines.append(f"- {t}")
            lines.append("Open applications (hint):")
            for a in self._open_apps[:20]:
                lines.append(f"- {a}")
            if self._last_mode:
                lines.append(f"Last mode hint: {self._last_mode.value}")
            return "\n".join(lines)


class LongTermMemory:
    """SQLite-backed metadata and embedding vectors with cosine retrieval."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or (settings.data_path / "memory.sqlite3")
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    id TEXT PRIMARY KEY,
                    source TEXT,
                    label TEXT,
                    payload TEXT,
                    created REAL
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    id TEXT PRIMARY KEY,
                    metadata_id TEXT,
                    dim INTEGER,
                    vector TEXT,
                    FOREIGN KEY(metadata_id) REFERENCES metadata(id)
                )
                """
            )
            c.commit()

    def write_metadata(
        self,
        source: str,
        label: str,
        payload: dict[str, Any],
    ) -> str:
        mid = str(uuid.uuid4())
        with self._lock:
            with self._connect() as c:
                c.execute(
                    "INSERT INTO metadata (id, source, label, payload, created) VALUES (?, ?, ?, ?, ?)",
                    (mid, source, label, json.dumps(payload), time.time()),
                )
                c.commit()
        return mid

    def write_embedding(self, metadata_id: str, vector: list[float]) -> str:
        eid = str(uuid.uuid4())
        with self._lock:
            with self._connect() as c:
                c.execute(
                    "INSERT INTO embeddings (id, metadata_id, dim, vector) VALUES (?, ?, ?, ?)",
                    (eid, metadata_id, len(vector), json.dumps(vector)),
                )
                c.commit()
        return eid

    def index_text_for_metadata(self, metadata_id: str, text: str) -> str:
        """Store embedding row linked to metadata (typically utterance text)."""
        return self.write_embedding(metadata_id, embed_text(text))

    def write_metadata_and_index_text(
        self,
        source: str,
        label: str,
        payload: dict[str, Any],
        text_to_embed: str,
    ) -> str:
        """Write metadata row and attach embedding for the given text."""
        mid = self.write_metadata(source, label, payload)
        self.index_text_for_metadata(mid, text_to_embed)
        return mid

    def retrieve_relevant(
        self,
        query_embedding: list[float] | None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return top metadata rows by cosine similarity when query_embedding set; else recent rows."""
        with self._lock:
            with self._connect() as c:
                if query_embedding:
                    rows = c.execute(
                        """
                        SELECT m.id, m.source, m.label, m.payload, e.vector
                        FROM metadata m
                        INNER JOIN embeddings e ON e.metadata_id = m.id
                        """
                    ).fetchall()
                else:
                    rows = c.execute(
                        """
                        SELECT id, source, label, payload FROM metadata
                        ORDER BY rowid DESC LIMIT ?
                        """,
                        (limit,),
                    ).fetchall()

        if not query_embedding:
            out: list[dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "id": r["id"],
                        "source": r["source"],
                        "label": r["label"],
                        "payload": json.loads(r["payload"] or "{}"),
                        "score": None,
                    }
                )
            return out

        scored: list[tuple[float, dict[str, Any]]] = []
        for r in rows:
            try:
                vec = json.loads(r["vector"])
                if not isinstance(vec, list):
                    continue
                score = cosine_similarity(query_embedding, [float(x) for x in vec])
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
            scored.append(
                (
                    score,
                    {
                        "id": r["id"],
                        "source": r["source"],
                        "label": r["label"],
                        "payload": json.loads(r["payload"] or "{}"),
                        "score": score,
                    },
                )
            )
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]


short_term = ShortTermMemory()
long_term = LongTermMemory()
