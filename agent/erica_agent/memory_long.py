from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any

from erica_agent.config import settings


class LongTermMemory:
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
        import time

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

    def retrieve_relevant(
        self,
        query_embedding: list[float] | None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Placeholder semantic retrieval: returns recent metadata rows if no embedding index."""
        with self._lock:
            with self._connect() as c:
                rows = c.execute(
                    "SELECT id, source, label, payload FROM metadata ORDER BY rowid DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": r["id"],
                    "source": r["source"],
                    "label": r["label"],
                    "payload": json.loads(r["payload"] or "{}"),
                }
            )
        return out


long_term = LongTermMemory()
