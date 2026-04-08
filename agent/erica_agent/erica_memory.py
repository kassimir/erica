"""Erica MemPalace facade: palace init, drawers, diary, KG, wake-up stack."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from erica_agent.config import settings
from erica_agent.embeddings import embed_text
from erica_agent.memory import long_term as sqlite_cache
from erica_agent.mempalace_client import MempalaceClient
from erica_agent.palace_config import (
    ERICA_FACTS,
    ERICA_IDENTITY,
    HALL_ERRORS,
    HALL_EVENTS,
    HALL_PREFERENCES,
    infer_room,
)

log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MEMORY_SEED_DIR = _REPO_ROOT / "memory"
_KG_PATH = Path.home() / ".mempalace" / "erica_knowledge_graph.sqlite3"


class EricaMemory:
    """MemPalace + KnowledgeGraph integration for Erica."""

    def __init__(self) -> None:
        self._palace_path = Path(
            settings.mempalace_palace_path
            if settings.mempalace_palace_path is not None
            else Path.home() / ".mempalace" / "erica_palace"
        ).expanduser()
        self._identity_path = (
            Path(settings.mempalace_identity_path).expanduser()
            if settings.mempalace_identity_path is not None
            else self._palace_path / "identity.txt"
        )
        self._client = MempalaceClient(
            palace_path=self._palace_path,
            identity_path=self._identity_path,
        )
        self._stack: Any = None
        self._kg: Any = None
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self._palace_path.mkdir(parents=True, exist_ok=True)
        self._seed_identity_file()
        self._seed_wing_config()
        self._init_stack()
        self._init_kg()
        self._seed_kg_facts()
        self._initialized = True
        log.info("EricaMemory initialized at %s", self._palace_path)

    def _seed_identity_file(self) -> None:
        seed = _MEMORY_SEED_DIR / "identity.txt"
        if seed.is_file():
            try:
                text = seed.read_text(encoding="utf-8")
            except OSError:
                text = ERICA_IDENTITY
        else:
            text = ERICA_IDENTITY
        if not self._identity_path.is_file() or self._identity_path.stat().st_size == 0:
            self._identity_path.parent.mkdir(parents=True, exist_ok=True)
            self._identity_path.write_text(text.strip() + "\n", encoding="utf-8")

    def _seed_wing_config(self) -> None:
        dst = self._palace_path / "wing_config.json"
        if dst.is_file():
            return
        seed = _MEMORY_SEED_DIR / "wing_config_seed.json"
        if seed.is_file():
            try:
                shutil.copyfile(seed, dst)
            except OSError:
                log.warning("Could not copy wing_config_seed.json")
        else:
            dst.write_text(
                json.dumps(
                    {
                        "default_wing": "wing_tasks",
                        "wings": {
                            "wing_user": {"type": "person", "keywords": ["user", "human", "chris"]},
                            "wing_tasks": {"type": "project", "keywords": ["task", "erica", "shell"]},
                            "wing_computer": {"type": "project", "keywords": ["pc", "windows", "machine"]},
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

    def _init_stack(self) -> None:
        try:
            from mempalace.layers import MemoryStack

            self._stack = MemoryStack(
                palace_path=str(self._palace_path),
                identity_path=str(self._identity_path),
            )
        except ImportError:
            log.warning("mempalace.layers.MemoryStack unavailable; wake_up_context will use L0 file only")
            self._stack = None

    def _init_kg(self) -> None:
        try:
            from mempalace.knowledge_graph import KnowledgeGraph

            _KG_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._kg = KnowledgeGraph(db_path=str(_KG_PATH))
        except ImportError:
            log.warning("mempalace.knowledge_graph unavailable")
            self._kg = None

    def _seed_kg_facts(self) -> None:
        if not self._kg:
            return
        for subj, pred, obj in ERICA_FACTS:
            try:
                self._kg.add_triple(subj, pred, obj, valid_from=date.today().isoformat())
            except Exception:
                log.debug("KG seed skip for %s %s %s", subj, pred, obj)

    def identity_l0(self) -> str:
        p = self._identity_path
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8").strip()[:4000]
            except OSError:
                pass
        return ERICA_IDENTITY.strip()

    def wake_up_context(self) -> str:
        if self._stack:
            try:
                return self._stack.wake_up()
            except Exception as e:
                log.warning("MemoryStack.wake_up failed: %s", e)
        return self.identity_l0()

    def recall(self, query: str, wing: str | None = None, room: str | None = None) -> list[str]:
        raw = self._client.search(query, wing=wing, room=room, limit=12)
        hits = raw.get("results") if isinstance(raw, dict) else None
        out: list[str] = []
        if isinstance(hits, list):
            for h in hits:
                if isinstance(h, dict) and h.get("text"):
                    line = str(h["text"]).strip()
                    if line:
                        out.append(line[:2000])
        if out:
            return out
        q_emb = embed_text(query) if query.strip() else None
        rows = sqlite_cache.retrieve_relevant(q_emb, limit=8)
        for r in rows:
            p = r.get("payload")
            if isinstance(p, dict) and p.get("text"):
                out.append(str(p["text"])[:2000])
        return out

    def add_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        valid_from: str | None = None,
    ) -> dict[str, Any]:
        if not self._kg:
            return {"ok": False, "error": "KnowledgeGraph unavailable"}
        tid = self._kg.add_triple(subject, predicate, obj, valid_from=valid_from)
        return {"ok": True, "triple_id": tid}

    def invalidate_fact(self, subject: str, predicate: str, obj: str) -> dict[str, Any]:
        if not self._kg:
            return {"ok": False, "error": "KnowledgeGraph unavailable"}
        self._kg.invalidate(subject, predicate, obj)
        return {"ok": True}

    def log_diary(self, entry: str, agent_name: str = "erica") -> dict[str, Any]:
        return self._client.diary_write(agent_name, entry, topic="session")

    def store_utterance(
        self,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        source: str = "session",
        label: str = "utterance",
    ) -> str:
        """Mirror MemoryBackend.write: file utterance in wing_tasks (or tagged wing)."""
        meta = dict(metadata or {})
        if tags:
            meta["tags"] = tags
        wing = "wing_tasks"
        room = label or "utterance"
        if tags:
            if tags[0].startswith("wing_"):
                wing = tags[0]
                room = tags[1] if len(tags) > 1 else "utterance"
            else:
                room = tags[0]
        r = self._client.add_drawer(
            wing,
            room,
            text,
            extra_meta={**meta, "hall": HALL_EVENTS, "type": "utterance"},
            added_by=source,
        )
        try:
            return sqlite_cache.write_metadata_and_index_text(
                source,
                label,
                {"text": text[:2000], **meta, "mempalace": r},
                text,
            )
        except Exception:
            log.exception("SQLite utterance cache failed")
            return str(r.get("drawer_id") or "")

    def save_interaction(
        self,
        user_input: str | None,
        erica_response: str,
        skill_id: str | None,
        status: str,
        results: list[dict[str, Any]] | None = None,
    ) -> None:
        wing, room = infer_room(skill_id or "unknown.skill")
        hall = HALL_ERRORS if status == "error" else HALL_EVENTS
        if results:
            for r in results:
                if r.get("ok") is False:
                    hall = HALL_ERRORS
                    break
        block = "\n".join(
            [
                f"user: {user_input or '(plan-only)'}",
                f"response: {erica_response[:4000]}",
                f"skill_id: {skill_id}",
                f"status: {status}",
                f"hall: {hall}",
            ]
        )
        meta = {
            "hall": hall,
            "type": "interaction",
            "status": status,
            "skill_id": skill_id or "",
        }
        r = self._client.add_drawer(
            wing,
            room,
            block,
            added_by="erica_agent",
            extra_meta=meta,
        )
        if not r.get("success"):
            log.debug("save_interaction drawer skipped: %s", r.get("error"))
        try:
            sqlite_cache.write_metadata_and_index_text(
                "erica_memory",
                "interaction",
                {"wing": wing, "room": room, "hall": hall, "mempalace": r},
                block,
            )
        except Exception:
            log.exception("SQLite mirror for interaction failed")
        self._kg_learn_from_interaction(user_input, skill_id, status, results)

    def _kg_learn_from_interaction(
        self,
        user_input: str | None,
        skill_id: str | None,
        status: str,
        results: list[dict[str, Any]] | None,
    ) -> None:
        if not self._kg or not user_input:
            return
        try:
            if status == "ok" and skill_id:
                self._kg.add_triple(
                    "User",
                    "last_successful_skill",
                    skill_id.replace(".", "_"),
                    valid_from=date.today().isoformat(),
                )
        except Exception:
            log.debug("KG interaction learn skipped", exc_info=True)

    def store_preference_fact(self, utterance: str) -> None:
        if not self._kg:
            return
        snippet = utterance.strip()[:500]
        try:
            self._kg.add_triple(
                "User",
                "stated_preference",
                snippet,
                valid_from=date.today().isoformat(),
            )
        except Exception:
            log.exception("Preference KG write failed")
        wing, room = ("wing_user", "preferences")
        self._client.add_drawer(
            wing,
            room,
            f"Preference: {snippet}",
            extra_meta={"hall": HALL_PREFERENCES, "type": "preference"},
        )


_erica: EricaMemory | None = None


def init_erica_memory() -> EricaMemory:
    global _erica
    _erica = EricaMemory()
    _erica.initialize()
    return _erica


def get_erica_memory() -> EricaMemory:
    global _erica
    if _erica is None:
        return init_erica_memory()
    return _erica
